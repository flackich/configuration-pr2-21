"""Stage 4: dependency-first topological order and cycle failures."""

import unittest

from src.order import OrderError, dependency_first_order


class OrderTests(unittest.TestCase):
    def test_dependencies_come_first(self):
        graph = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        order = dependency_first_order(graph)
        self.assertEqual(set(order), set(graph))
        for parent, dependencies in graph.items():
            for dependency in dependencies:
                self.assertLess(order.index(dependency), order.index(parent))

    def test_cycle_is_explicit(self):
        with self.assertRaisesRegex(OrderError, "циклический"):
            dependency_first_order({"A": ["B"], "B": ["A"]})

    def test_root_only(self):
        self.assertEqual(dependency_first_order({"A": []}), ["A"])


if __name__ == "__main__":
    unittest.main()
