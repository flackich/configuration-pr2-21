"""Iterative DFS construction of dependency graphs and cycle detection."""

import json
import re
from pathlib import Path

from src.cli import Config
from src.registry import RegistryClient


Graph = dict[str, list[str]]


class GraphError(ValueError):
    """The test graph is malformed or the root is unavailable."""


def load_test_repository(path: str) -> Graph:
    """Load {"A": ["B", ...]} from JSON and validate uppercase labels."""
    try:
        content = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise GraphError(
            "Не удалось прочитать тестовый граф: " + str(error)
        ) from error
    if not isinstance(content, dict):
        raise GraphError("Тестовый граф должен быть JSON-объектом")
    answer = {}
    for name, neighbors in content.items():
        if not isinstance(name, str) or not re.fullmatch(r"[A-Z]+", name):
            raise GraphError("Имя вершины должно состоять из A-Z: " + str(name))
        if not isinstance(neighbors, list):
            raise GraphError("Список зависимостей обязателен для " + name)
        for dependency in neighbors:
            if (
                not isinstance(dependency, str)
                or not re.fullmatch(r"[A-Z]+", dependency)
            ):
                raise GraphError("Имя зависимости должно состоять из A-Z")
        answer[name] = list(dict.fromkeys(neighbors))
    return answer


def build_test_graph(config: Config) -> tuple[str, Graph]:
    """Traverse a fixture using an explicit stack, respecting depth/filter."""
    source = load_test_repository(config.repository)
    if config.package not in source:
        raise GraphError("Исходный пакет отсутствует в тестовом графе")
    return _traverse_fixture(
        source, config.package, config.max_depth, config.exclude
    )


def _traverse_fixture(
    source: Graph, root: str, max_depth: int, exclude: str
) -> tuple[str, Graph]:
    if exclude and exclude in root:
        raise GraphError("Исходный пакет исключён фильтром")
    graph: Graph = {}
    best_depth: dict[str, int] = {}
    stack = [(root, 0)]
    while stack:
        name, depth = stack.pop()
        if depth > max_depth or (exclude and exclude in name):
            continue
        if name in best_depth and best_depth[name] <= depth:
            continue
        best_depth[name] = depth
        filtered = _fixture_dependencies(
            source, name, depth, max_depth, exclude
        )
        graph[name] = filtered
        stack.extend((item, depth + 1) for item in reversed(filtered))
    return root, graph


def _fixture_dependencies(
    source: Graph, name: str, depth: int, max_depth: int, exclude: str
) -> list[str]:
    """Select fixture edges within the depth limit, applying the filter."""
    if depth >= max_depth:
        return []
    return [
        item for item in source.get(name, [])
        if not exclude or exclude not in item
    ]


def _resolve_alias(name: str, requirement: str) -> tuple[str, str]:
    """Handle npm aliases such as alias: 'npm:real-package@^1'."""
    if not requirement.startswith("npm:"):
        return name, requirement
    package_and_spec = requirement[4:]
    package, sep, spec = package_and_spec.rpartition("@")
    if not sep or not package:
        raise GraphError("Неподдерживаемый npm alias: " + requirement)
    return package, spec or "latest"


def build_registry_graph(
    config: Config, client: RegistryClient
) -> tuple[str, Graph]:
    """Resolve npm package versions and build an iterative depth-limited DFS."""
    if config.exclude and config.exclude in config.package:
        raise GraphError("Исходный пакет исключён фильтром")
    root = ""
    graph: Graph = {}
    best_depth: dict[str, int] = {}
    stack = [(config.package, "latest", 0)]
    while stack:
        name, requirement, depth = stack.pop()
        if depth > config.max_depth or (
            config.exclude and config.exclude in name
        ):
            continue
        version, requirements = client.resolve(name, requirement)
        node = name + "@" + version
        if not root:
            root = node
        if node in best_depth and best_depth[node] <= depth:
            continue
        best_depth[node] = depth
        edges, children = _registry_dependencies(
            config, client, requirements, depth
        )
        graph[node] = edges
        stack.extend(reversed(children))
    return root, graph


def _registry_dependencies(
    config: Config, client: RegistryClient,
    requirements: dict[str, str], depth: int,
) -> tuple[list[str], list[tuple[str, str, int]]]:
    """Resolve filtered children, leaving depth-boundary nodes as leaves."""
    if depth >= config.max_depth:
        return [], []
    edges: list[str] = []
    children = []
    for dependency, spec in sorted(requirements.items()):
        target, constraint = _resolve_alias(dependency, spec)
        if config.exclude and config.exclude in target:
            continue
        dep_version, _ = client.resolve(target, constraint)
        edges.append(target + "@" + dep_version)
        children.append((target, constraint, depth + 1))
    return list(dict.fromkeys(edges)), children


def find_cycles(graph: Graph) -> list[list[str]]:
    """Return back-edge cycles using iterative colored DFS (no recursion)."""
    colors: dict[str, int] = {}
    cycles: list[list[str]] = []
    for root in graph:
        if colors.get(root, 0):
            continue
        colors[root] = 1
        stack = [(root, iter(graph.get(root, [])))]
        path = [root]
        while stack:
            name, neighbors = stack[-1]
            try:
                neighbor = next(neighbors)
            except StopIteration:
                colors[name] = 2
                stack.pop()
                path.pop()
                continue
            status = colors.get(neighbor, 0)
            if status == 1:
                cycles.append(path[path.index(neighbor):] + [neighbor])
            elif status == 0:
                colors[neighbor] = 1
                path.append(neighbor)
                stack.append((neighbor, iter(graph.get(neighbor, []))))
    return cycles
