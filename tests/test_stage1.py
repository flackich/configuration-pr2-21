"""Stage 1: validation and CLI configuration."""

import tempfile
import unittest
from pathlib import Path

from src.cli import parse_config


class ConfigTests(unittest.TestCase):
    def test_valid_registry_configuration(self):
        args = [
            "--package", "@babel/core",
            "--repository", "https://registry.npmjs.org",
            "--max-depth", "3", "--exclude", "test",
        ]
        config = parse_config(args)
        self.assertEqual(config.package, "@babel/core")
        self.assertEqual(config.max_depth, 3)
        self.assertEqual(config.exclude, "test")

    def test_test_mode_path(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "graph.json"
            path.write_text("{}", encoding="utf-8")
            config = parse_config([
                "--package", "A", "--repository", str(path), "--test-mode",
            ])
            self.assertTrue(config.test_mode)

    def test_invalid_parameters(self):
        cases = [
            ["--repository", "https://registry.npmjs.org"],
            ["--package", "a", "--repository", "not-an-url"],
            [
                "--package", "a", "--repository", "http://host",
                "--max-depth", "-1",
            ],
            ["--package", "bad name", "--repository", "http://host"],
            ["--package", "a", "--repository", "missing.json", "--test-mode"],
        ]
        for args in cases:
            with self.subTest(args=args), self.assertRaises(SystemExit):
                parse_config(args)



if __name__ == "__main__":
    unittest.main()
