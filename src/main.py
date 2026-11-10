"""Final CLI: npm dependency graph, loading order, D2 visualization."""

import sys
from pathlib import Path

from src.cli import parse_config
from src.d2 import to_d2
from src.graph import (
    GraphError, build_registry_graph, build_test_graph, find_cycles,
)
from src.order import OrderError, dependency_first_order
from src.registry import RegistryClient, RegistryError


def _show_graph(root: str, graph: dict[str, list[str]]) -> None:
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


def _show_order(graph: dict[str, list[str]]) -> None:
    try:
        order = dependency_first_order(graph)
    except OrderError as error:
        print("Порядок загрузки не определён:", error)
    else:
        print("Порядок загрузки (зависимости раньше пакетов):")
        for index, name in enumerate(order, 1):
            print(f"  {index}. {name}")


def main(argv: list[str] | None = None) -> int:
    config = parse_config(argv)
    try:
        if config.test_mode:
            root, graph = build_test_graph(config)
        else:
            root, graph = build_registry_graph(
                config, RegistryClient(config.repository)
            )
        d2_source = to_d2(graph)
        if config.output:
            target = Path(config.output)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(d2_source, encoding="utf-8")
    except (RegistryError, GraphError, OSError) as error:
        print("Ошибка:", error, file=sys.stderr)
        return 1
    if config.only_d2:
        print(d2_source, end="")
        return 0
    _show_graph(root, graph)
    _show_order(graph)
    print("\nОписание графа на языке D2:\n")
    print(d2_source, end="")
    if config.output:
        print("D2 сохранён:", config.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
