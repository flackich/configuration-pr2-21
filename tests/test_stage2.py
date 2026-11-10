"""Stage 2: mocked npm registry, semver, direct dependencies and errors."""

import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from src.registry import RegistryClient, RegistryError
from src.semver import satisfies


PACKAGE = {
    "dist-tags": {"latest": "2.3.0"},
    "versions": {
        "1.0.0": {"dependencies": {"old": "^1.0.0"}},
        "2.0.0": {"dependencies": {"shared": "~1.0.0"}},
        "2.3.0": {"dependencies": {"left-pad": "^1.3.0"}},
    },
}


class RegistryTests(unittest.TestCase):
    def test_latest_and_range_and_cache(self):
        with patch("src.registry.urlopen", return_value=io.BytesIO(
            json.dumps(PACKAGE).encode("utf-8")
        )) as request:
            client = RegistryClient("https://registry.npmjs.org")
            self.assertEqual(client.resolve("sample"), ("2.3.0", {
                "left-pad": "^1.3.0"
            }))
            self.assertEqual(client.resolve("sample", "^2.0.0")[0], "2.3.0")
            self.assertEqual(request.call_count, 1)

    def test_registry_error(self):
        error = HTTPError("http://host/a", 404, "Not Found", None, None)
        with patch("src.registry.urlopen", side_effect=error):
            with self.assertRaises(RegistryError):
                RegistryClient("http://host").resolve("a")

    def test_semver_common_ranges(self):
        self.assertTrue(satisfies("1.9.0", "^1.2.3"))
        self.assertFalse(satisfies("2.0.0", "^1.2.3"))
        self.assertTrue(satisfies("0.2.9", "^0.2.1"))
        self.assertFalse(satisfies("0.3.0", "^0.2.1"))
        self.assertTrue(satisfies("1.2.9", "~1.2"))
        self.assertFalse(satisfies("1.3.0", "~1.2"))
        self.assertTrue(satisfies("2.7.0", ">=2 <3"))
        self.assertTrue(satisfies("4.0.0", "^1 || ^4"))
        self.assertFalse(satisfies("1.2.3-beta.1", "^1"))


if __name__ == "__main__":
    unittest.main()
