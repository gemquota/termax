from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "experimental" / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PULSE = load("termax_pulse_test", "termax_pulse.py")
REEF = load("termax_aquarium_test", "termax_aquarium.py")
EXPLORER = load("termax_explorer_test", "termax_explore.py")


class PulseTests(unittest.TestCase):
    def test_classification(self):
        self.assertEqual(PULSE.classify("3 tests passed"), "ok")
        self.assertEqual(PULSE.classify("WARNING: deprecated"), "warn")
        self.assertEqual(PULSE.classify("Traceback: exception"), "bad")
        self.assertEqual(PULSE.classify("collecting tests"), "info")

    def test_waveform_has_bounded_length(self):
        wave = PULSE.waveform(12, 24)
        self.assertEqual(len(wave), 24)


class AquariumTests(unittest.TestCase):
    def test_events_change_reef_stability(self):
        reef = REEF.Aquarium()
        reef.render("ok")
        self.assertEqual(reef.health, 2)
        reef.render("bad")
        self.assertEqual(reef.health, -1)

    def test_scene_is_multiline(self):
        self.assertGreater(len(REEF.Aquarium().render("run").splitlines()), 3)


class ExplorerTests(unittest.TestCase):
    def test_lists_directories_before_files_and_filters(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "z-file.txt").write_text("x")
            (root / "a-dir").mkdir()
            (root / ".hidden").write_text("x")
            explorer = EXPLORER.Explorer(root)
            self.assertEqual(explorer.entries[0].name, "a-dir")
            self.assertNotIn(".hidden", [p.name for p in explorer.entries])
            explorer.hidden = True
            explorer.query = "hidden"
            explorer.refresh()
            self.assertEqual([p.name for p in explorer.entries], [".hidden"])


if __name__ == "__main__":
    unittest.main()
