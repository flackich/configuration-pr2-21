"""Regression checks for graph and semver helpers extracted after review."""

import unittest
from unittest.mock import Mock, patch

from src.cli import Config
from src.graph import GraphError, build_registry_graph, build_test_graph
from src.semver import VersionRangeError, satisfies


class SemverRegressionTests(unittest.TestCase):
    def test_comparators_and_partial_boundaries(self):
        cases = [
            (">=1.2.3", "1.2.3", True), (">=1.2.3", "1.2.2", False),
            (">1.2.3", "1.2.3", False), (">1.2.3", "1.2.4", True),
            ("<=1.2.3", "1.2.3", True), ("<=1.2.3", "1.2.4", False),
            ("<1.2.3", "1.2.3", False), ("<1.2.3", "1.2.2", True),
            ("=1.2.3", "1.2.3", True), ("=1.2.3", "1.2.4", False),
            ("1.2.3", "1.2.3", True), ("1.2.3", "1.2.4", False),
            ("1.2.x", "1.2.9", True), ("1.2.x", "1.3.0", False),
            ("1", "1.9.9", True), ("1", "2.0.0", False),
            ("^0.0", "0.0.9", True), ("^0.0", "0.1.0", False),
            ("^0.0.1", "0.0.1", True), ("^0.0.1", "0.0.2", False),
            ("1.0.0 - 2.0.0", "2.0.0", True),
            ("1.0.0 - 2.0.0", "2.0.1", False),
            ("1.2.3+build", "1.2.3", True), ("x", "9.0.0", True),
        ]
        for expression, version, expected in cases:
            with self.subTest(expression=expression, version=version):
                self.assertEqual(satisfies(version, expression), expected)

    def test_invalid_range_errors_are_preserved(self):
        for expression in ("1.2.3.4", "1 - 2 - 3", "bad", "file:../lib"):
            with self.subTest(expression=expression):
                with self.assertRaises(VersionRangeError):
                    satisfies("1.2.3", expression)


class GraphRegressionTests(unittest.TestCase):
    def test_shorter_path_reopens_shared_node_in_both_sources(self):
        source = {"A": ["B", "C"], "B": ["D"], "D": ["C"],
                  "C": ["E"], "E": ["F"], "F": []}
        expected = {"A": ["B", "C"], "B": ["D"], "D": ["C"],
                    "C": ["E"], "E": ["F"], "F": []}
        config = Config("A", "unused.json", True, 3, "")
        with patch("src.graph.load_test_repository", return_value=source):
            root, graph = build_test_graph(config)
        self.assertEqual(root, "A")
        self.assertEqual(graph, expected)
        client = Mock()
        client.resolve.side_effect = lambda name, spec: (
            "1.0.0", dict.fromkeys(source[name], "*")
        )
        root, graph = build_registry_graph(config, client)
        versioned = {name + "@1.0.0": [item + "@1.0.0" for item in edges]
                     for name, edges in expected.items()}
        self.assertEqual(root, "A@1.0.0")
        self.assertEqual(graph, versioned)

    def test_registry_filter_aliases_and_depth_before_requests(self):
        requirements = {"alias": "npm:keep@^1", "keep": "^1", "skip": "*"}
        client = Mock()
        client.resolve.side_effect = lambda name, spec: (
            "1.0.0", requirements if name == "root" else {}
        )
        config = Config("root", "https://example.org", False, 1, "skip")
        _, graph = build_registry_graph(config, client)
        self.assertEqual(graph, {"root@1.0.0": ["keep@1.0.0"], "keep@1.0.0": []})
        self.assertNotIn("skip", [call.args[0] for call in client.resolve.call_args_list])
        client.reset_mock()
        config = Config("root", "https://example.org", False, 0, "")
        _, graph = build_registry_graph(config, client)
        self.assertEqual(graph, {"root@1.0.0": []})
        client.resolve.assert_called_once_with("root", "latest")
        client.reset_mock()
        config = Config("root", "https://example.org", False, 1, "root")
        with self.assertRaises(GraphError):
            build_registry_graph(config, client)
        client.resolve.assert_not_called()


if __name__ == "__main__":
    unittest.main()
