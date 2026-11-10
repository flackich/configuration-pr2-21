"""Entry point. Stage 1 prints validated configuration."""

from src.cli import parse_config


def main(argv: list[str] | None = None) -> int:
    config = parse_config(argv)
    print("package:", config.package)
    print("repository:", config.repository)
    print("test_mode:", config.test_mode)
    print("max_depth:", config.max_depth)
    print("exclude:", config.exclude or "(не задано)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
