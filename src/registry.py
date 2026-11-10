"""Read npm registry JSON directly, without invoking npm or dependencies APIs."""

import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from src.semver import VersionRangeError, satisfies, version_key


MAX_RESPONSE_BYTES = 25 * 1024 * 1024


class RegistryError(RuntimeError):
    """Registry returned unavailable or invalid package metadata."""


class RegistryClient:
    """Minimal npm package metadata reader using only Python's stdlib."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.cache: dict[str, dict] = {}

    def _read_json(self, name: str) -> dict:
        url = self.base_url + "/" + quote(name, safe="")
        request = Request(
            url, headers={"Accept": "application/vnd.npm.install-v1+json"}
        )
        try:
            with urlopen(request, timeout=15) as response:
                data = response.read(MAX_RESPONSE_BYTES + 1)
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            raise RegistryError(f"Ошибка загрузки {name}: {error}") from error
        if len(data) > MAX_RESPONSE_BYTES:
            raise RegistryError("Ответ реестра слишком большой: " + name)
        try:
            content = json.loads(data.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as error:
            raise RegistryError("Некорректный JSON для " + name) from error
        if not isinstance(content, dict) or not isinstance(content.get("versions"), dict):
            raise RegistryError("Нет списка версий в метаданных: " + name)
        return content

    def metadata(self, name: str) -> dict:
        if name not in self.cache:
            self.cache[name] = self._read_json(name)
        return self.cache[name]

    def resolve(self, name: str, requirement: str = "latest") -> tuple[str, dict]:
        """Return (chosen version, dependencies dict), choosing latest match."""
        metadata = self.metadata(name)
        versions = metadata["versions"]
        tags = metadata.get("dist-tags", {})
        requested = tags.get(requirement, requirement)
        candidates = []
        for version in versions:
            try:
                if satisfies(version, requested):
                    candidates.append(version)
            except VersionRangeError as error:
                raise RegistryError(f"{name}: {error}") from error
        if not candidates:
            raise RegistryError(f"Не найдена версия {name}, подходящая под {requirement}")
        chosen = max(candidates, key=version_key)
        data = versions[chosen]
        dependencies = data.get("dependencies", {})
        if not isinstance(dependencies, dict):
            raise RegistryError("Некорректные зависимости для " + name)
        return chosen, dependencies
