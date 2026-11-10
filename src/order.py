"""Deterministic dependency-first postorder using iterative DFS."""

from src.graph import Graph, find_cycles


class OrderError(ValueError):
    """A topological loading order does not exist due to a cycle."""


def dependency_first_order(graph: Graph) -> list[str]:
    """Return dependencies before dependents for an acyclic graph.

    npm itself does not guarantee one installation order; this is a valid
    deterministic topological order of the analyzed dependency graph.
    """
    cycles = find_cycles(graph)
    if cycles:
        raise OrderError("Нельзя упорядочить циклический граф: " +
                         " -> ".join(cycles[0]))
    colors: dict[str, int] = {}
    result: list[str] = []
    for root in graph:
        if colors.get(root):
            continue
        colors[root] = 1
        stack = [(root, iter(graph[root]))]
        while stack:
            vertex, neighbors = stack[-1]
            try:
                neighbor = next(neighbors)
            except StopIteration:
                colors[vertex] = 2
                result.append(vertex)
                stack.pop()
                continue
            if not colors.get(neighbor):
                colors[neighbor] = 1
                stack.append((neighbor, iter(graph.get(neighbor, []))))
    return result
