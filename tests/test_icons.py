"""Unit tests for pure-Python pixel icon generator."""

import tempfile
import unittest
from pathlib import Path

from apps.icons import generate_basketball_gif, generate_cake_gif, generate_candle_gif


class TestIconGeneration(unittest.TestCase):
    def test_generate_candle_gif(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "candle.gif"
            generate_candle_gif(out)
            self.assertTrue(out.exists())
            content = out.read_bytes()
            self.assertTrue(content.startswith(b"GIF89a"))
            self.assertGreater(len(content), 100)

    def test_generate_cake_gif(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "cake.gif"
            generate_cake_gif(out)
            self.assertTrue(out.exists())
            content = out.read_bytes()
            self.assertTrue(content.startswith(b"GIF89a"))
            self.assertGreater(len(content), 100)

    def test_generate_basketball_gif(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "basketball.gif"
            generate_basketball_gif(out)
            self.assertTrue(out.exists())
            content = out.read_bytes()
            self.assertTrue(content.startswith(b"GIF89a"))
            self.assertGreater(len(content), 80)


if __name__ == "__main__":
    unittest.main()
