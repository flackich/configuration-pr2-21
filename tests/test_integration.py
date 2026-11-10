"""Offline end-to-end pipeline with mocked HTTP npm registry responses."""

import contextlib
import io
import json
import unittest
from urllib.parse import unquote, urlparse
from unittest.mock import patch

from src.main import main


METADATA = {
    "a": {
        "dist-tags": {"latest": "1.0.0"},
        "versions": {"1.0.0": {
            "dependencies": {"b": "^1.0.0", "c": "^2.0.0"}
        }},
    },
    "b": {
        "dist-tags": {"latest": "1.0.0"},
        "versions": {"1.0.0": {
            "dependencies": {"c": "^1.0.0"}
        }},
    },
    "c": {
        "dist-tags": {"latest": "2.0.0"},
        "versions": {
            "1.0.0": {"dependencies": {}},
            "2.0.0": {"dependencies": {}},
        },
    },
}


def fake_open(request, timeout=15):
    """Emulate npm registry metadata without contacting the internet."""
    name = unquote(urlparse(request.full_url).path.lstrip("/"))
    return io.BytesIO(json.dumps(METADATA[name]).encode("utf-8"))


class IntegrationTests(unittest.TestCase):
    def test_complete_registry_pipeline(self):
        stdout = io.StringIO()
        with patch("src.registry.urlopen", side_effect=fake_open):
            with contextlib.redirect_stdout(stdout):
                result = main([
                    "--package", "a", "--repository", "https://mock.registry",
                    "--max-depth", "3",
                ])
        self.assertEqual(result, 0)
        output = stdout.getvalue()
        self.assertIn("a@1.0.0 -> b@1.0.0", output)
        self.assertIn("a@1.0.0 -> c@2.0.0", output)
        self.assertIn("b@1.0.0 -> c@1.0.0", output)
        self.assertIn('"a@1.0.0" -> "c@2.0.0"', output)
        self.assertIn("Порядок загрузки", output)


if __name__ == "__main__":
    unittest.main()
