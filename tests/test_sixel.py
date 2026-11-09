from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "experimental" / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SIXEL = load("termax_sixel_test", "termax_sixel.py")
EXPLORER = load("termax_explorer_sixel_test", "termax_explore.py")


class SixelTests(unittest.TestCase):
    def test_no_output_to_non_tty(self):
        with patch.object(SIXEL.sys.stdout, "isatty", return_value=False):
            self.assertFalse(SIXEL.render_sixel(Path("image.png")))

    def test_missing_encoders_fall_back(self):
        with patch.object(SIXEL.sys.stdout, "isatty", return_value=True), \
             patch.object(SIXEL.shutil, "which", return_value=None):
            self.assertFalse(SIXEL.render_sixel(Path("image.png")))

    def test_explorer_sixel_mode_defaults_off(self):
        with tempfile.TemporaryDirectory() as temp:
            explorer = EXPLORER.Explorer(Path(temp))
            self.assertFalse(explorer.sixel)


if __name__ == "__main__":
    unittest.main()
