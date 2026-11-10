"""Parse and validate CLI configuration for the npm dependency analyzer."""

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


NAME_PATTERN = re.compile(r"^(?:@[a-z0-9._-]+/)?[a-zA-Z0-9._-]+$")


@dataclass(frozen=True)
class Config:
    package: str
    repository: str
    test_mode: bool
    max_depth: int
    exclude: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Практическая №2, вариант 21: граф зависимостей npm"
    )
    parser.add_argument("--package", required=True, help="имя npm-пакета")
    parser.add_argument(
        "--repository", required=True,
        help="URL npm registry или путь к тестовому JSON",
    )
    parser.add_argument(
        "--test-mode", action="store_true", help="использовать тестовый граф"
    )
    parser.add_argument(
        "--max-depth", type=int, default=2,
        help="максимальная глубина графа; 0 — только исходный пакет",
    )
    parser.add_argument(
        "--exclude", default="", help="подстрока для исключения пакетов"
    )
    return parser


def parse_config(argv: list[str] | None = None) -> Config:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not NAME_PATTERN.fullmatch(args.package):
        parser.error("некорректное имя пакета")
    if args.max_depth < 0:
        parser.error("--max-depth не может быть отрицательным")
    if args.test_mode:
        path = Path(args.repository)
        if not path.is_file():
            parser.error("тестовый файл не найден: " + str(path))
        if path.suffix.lower() != ".json":
            parser.error("тестовый репозиторий должен быть JSON-файлом")
    else:
        parsed = urlparse(args.repository)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            parser.error("--repository должен быть URL http(s)")
    return Config(
        package=args.package,
        repository=args.repository,
        test_mode=args.test_mode,
        max_depth=args.max_depth,
        exclude=args.exclude,
    )
