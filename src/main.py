"""Stage 3: build transitive dependency graphs using iterative DFS."""

import sys

from src.cli import parse_config
from src.graph import GraphError, build_registry_graph, build_test_graph, find_cycles
from src.registry import RegistryClient, RegistryError


def main(argv: list[str] | None = None) -> int:
    config = parse_config(argv)
    try:
        if config.test_mode:
            root, graph = build_test_graph(config)
        else:
            root, graph = build_registry_graph(
                config, RegistryClient(config.repository)
            )
    except (RegistryError, GraphError) as error:
        print("Ошибка:", error, file=sys.stderr)
        return 1
    print("Граф зависимостей для", root)
    for name, dependencies in graph.items():
        for dependency in dependencies:
            print("  " + name + " -> " + dependency)
    cycles = find_cycles(graph)
    if cycles:
        print("Найдены циклы:")
        for cycle in cycles:
            print("  " + " -> ".join(cycle))
    else:
        print("Циклы не обнаружены")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
