"""Stage 3: iterative DFS, cycles, filtering, depth and fixtures."""

import tempfile
import unittest
from pathlib import Path

from src.cli import Config
from src.graph import (
    GraphError, build_registry_graph, build_test_graph, find_cycles,
    load_test_repository,
)


FIXTURES = Path(__file__).resolve().parent.parent / "test_data"


def fixture(name, max_depth=3, exclude=""):
    return Config("A", str(FIXTURES / name), True, max_depth, exclude)


class MockRegistry:
    def __init__(self):
        self.dep = {
            "a": {"b": "^1.0.0", "c": "^1.0.0"},
            "b": {"c": "^1.0.0"},
            "c": {"a": "^1.0.0"},
        }

    def resolve(self, name, requirement="latest"):
        return "1.0.0", self.dep[name]


class GraphTests(unittest.TestCase):
    def test_simple_dag(self):
        root, graph = build_test_graph(fixture("simple.json"))
        self.assertEqual(root, "A")
        self.assertEqual(graph["A"], ["B", "C"])
        self.assertEqual(set(graph), {"A", "B", "C", "D"})
        self.assertFalse(find_cycles(graph))

    def test_depth_and_exclusion(self):
        _, graph = build_test_graph(fixture("deep.json", 1))
        self.assertEqual(set(graph), {"A", "B", "E"})
        self.assertEqual(graph["B"], [])
        _, filtered = build_test_graph(fixture("simple.json", 3, "C"))
        self.assertNotIn("C", filtered)
        self.assertEqual(filtered["A"], ["B"])

    def test_cycle(self):
        _, graph = build_test_graph(fixture("cycle.json", 5))
        self.assertEqual(find_cycles(graph), [["A", "B", "C", "A"]])

    def test_bad_fixture(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "bad.json"
            file.write_text('{"bad-name": ["B"]}', encoding="utf-8")
            with self.assertRaises(GraphError):
                load_test_repository(str(file))

    def test_registry_iterative_and_versioned(self):
        config = Config("a", "http://localhost", False, 3, "")
        root, graph = build_registry_graph(config, MockRegistry())
        self.assertEqual(root, "a@1.0.0")
        self.assertIn("b@1.0.0", graph["a@1.0.0"])
        self.assertTrue(find_cycles(graph))


if __name__ == "__main__":
    unittest.main()
