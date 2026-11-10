"""D2 source generation for the npm dependency graph."""

from src.graph import Graph


def _quote(label: str) -> str:
    escaped = label.replace("\\", "\\\\").replace('"', '\\"')
    return '"' + escaped + '"'


def to_d2(graph: Graph) -> str:
    """Produce valid D2 nodes/edges; arrow points to a dependency."""
    lines = ["direction: right", ""]
    for node in sorted(graph):
        lines.append(_quote(node))
    if graph:
        lines.append("")
    for node in sorted(graph):
        for dependency in sorted(graph[node]):
            lines.append(_quote(node) + " -> " + _quote(dependency))
    return "\n".join(lines) + "\n"
