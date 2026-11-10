"""A documented subset of npm semver for common registry version ranges.

Supports exact versions, ^, ~, comparators, wildcard parts, OR and tags
(the latter are resolved in RegistryClient). Exotic npm protocols are rejected.
"""

import re


VERSION = re.compile(
    r"^v?(\d+)(?:\.(\d+))?(?:\.(\d+))?"
    r"(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$"
)


class VersionRangeError(ValueError):
    """A version range has unsupported or invalid syntax."""


def parse_version(text: str) -> tuple[int, int, int, str]:
    match = VERSION.fullmatch(text)
    if not match:
        raise VersionRangeError("Некорректная версия: " + text)
    major, minor, patch, prerelease = match.groups()
    return int(major), int(minor or 0), int(patch or 0), prerelease or ""


def version_key(version: str) -> tuple:
    major, minor, patch, pre = parse_version(version)
    if not pre:
        return major, minor, patch, 1, ()
    parts = tuple(
        (0, int(p)) if p.isdigit() else (1, p) for p in pre.split(".")
    )
    return major, minor, patch, 0, parts


def _partial_bound(value: str) -> tuple[tuple[int, int, int], int]:
    parts = value.lstrip("v").split(".")
    if not 1 <= len(parts) <= 3:
        raise VersionRangeError("Некорректный диапазон: " + value)
    nums = []
    for part in parts:
        if part.lower() in {"x", "*", ""}:
            break
        if not part.isdecimal():
            raise VersionRangeError("Неизвестный диапазон: " + value)
        nums.append(int(part))
    return tuple((nums + [0] * 3)[:3]), len(nums)


def _caret_upper(version: tuple[int, int, int], width: int) -> tuple:
    major, minor, patch = version
    if major:
        return major + 1, 0, 0
    if width == 1:
        return 1, 0, 0
    if minor:
        return 0, minor + 1, 0
    if width == 2:
        return 0, 1, 0
    return 0, 0, patch + 1


def _tilde_upper(version: tuple[int, int, int], width: int) -> tuple:
    major, minor, _ = version
    return (major + 1, 0, 0) if width == 1 else (major, minor + 1, 0)


def _matches_token(version: tuple[int, int, int], token: str) -> bool:
    if token.lower() in {"*", "x"}:
        return True
    if token.startswith("^"):
        low, width = _partial_bound(token[1:])
        return low <= version < _caret_upper(low, width)
    if token.startswith("~"):
        low, width = _partial_bound(token[1:])
        return low <= version < _tilde_upper(low, width)
    match = re.fullmatch(r"(>=|<=|>|<|=)?(.+)", token)
    if match is None:
        raise VersionRangeError("Некорректный диапазон: " + token)
    operation, raw = match.groups()
    if "-" in raw or "+" in raw:
        target = parse_version(raw)[:3]
        width = 3
    else:
        target, width = _partial_bound(raw)
    if operation == ">=":
        return version >= target
    if operation == ">":
        return version > target
    if operation == "<=":
        return version <= target
    if operation == "<":
        return version < target
    if operation == "=":
        return version == target
    if width == 0:
        return True
    if width < 3:
        upper = _tilde_upper(target, width)
        return target <= version < upper
    return version == target


def satisfies(version: str, expression: str) -> bool:
    """Match a subset of common npm semver constraints."""
    expr = expression.strip()
    if expr in {"", "*"}:
        return "-" not in version
    if expr.startswith(("file:", "git+", "workspace:", "link:")):
        raise VersionRangeError("Неподдерживаемый протокол версии: " + expr)
    base = parse_version(version)
    if base[3] and "-" not in expr:
        return False
    for alternate in expr.split("||"):
        text = alternate.strip()
        if " - " in text:
            bounds = text.split(" - ")
            if len(bounds) != 2:
                raise VersionRangeError("Некорректный диапазон: " + text)
            text = ">=" + bounds[0] + " <=" + bounds[1]
        tokens = text.replace(",", " ").split()
        if all(_matches_token(base[:3], token) for token in tokens):
            return True
    return False
