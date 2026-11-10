"""Stage 2: display direct npm dependencies returned by the registry."""

import sys

from src.cli import parse_config
from src.registry import RegistryClient, RegistryError


def main(argv: list[str] | None = None) -> int:
    config = parse_config(argv)
    if config.test_mode:
        print("Тестовый режим будет добавлен на этапе 3", file=sys.stderr)
        return 2
    try:
        version, dependencies = RegistryClient(config.repository).resolve(config.package)
    except RegistryError as error:
        print("Ошибка:", error, file=sys.stderr)
        return 1
    print(f"Прямые зависимости {config.package}@{version}:")
    for name, requirement in sorted(dependencies.items()):
        print(f"  {name}: {requirement}")
    if not dependencies:
        print("  (нет прямых зависимостей)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
