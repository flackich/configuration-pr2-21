"""Stage 5: D2 node/edge generation and output formatting."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from src.d2 import to_d2
from src.main import main


ROOT = Path(__file__).resolve().parent.parent


class D2Tests(unittest.TestCase):
    def test_edges_and_isolated_nodes(self):
        text = to_d2({"A": ["B", "C"], "B": [], "C": []})
        self.assertIn('"A" -> "B"', text)
        self.assertIn('"A" -> "C"', text)
        self.assertIn('"B"', text)
        self.assertTrue(text.startswith("direction: right"))

    def test_escape_special_names(self):
        text = to_d2({'some"name': ["@scope/lib@1.0.0"]})
        self.assertIn('"some\\"name"', text)
        self.assertIn('"@scope/lib@1.0.0"', text)

    def test_only_d2_and_file_output(self):
        with tempfile.TemporaryDirectory() as directory:
            saved = Path(directory) / "graph.d2"
            captured = io.StringIO()
            with contextlib.redirect_stdout(captured):
                result = main([
                    "--package", "A", "--repository",
                    str(ROOT / "test_data/simple.json"), "--test-mode",
                    "--max-depth", "3", "--only-d2",
                    "--output", str(saved),
                ])
            self.assertEqual(result, 0)
            self.assertEqual(
                saved.read_text(encoding="utf-8"), captured.getvalue()
            )
            self.assertNotIn("Граф зависимостей", captured.getvalue())


if __name__ == "__main__":
    unittest.main()
