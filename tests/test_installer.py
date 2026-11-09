from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "install.py"


class InstallerSafetyTests(unittest.TestCase):
    def run_installer(self, *args: str, home: Path):
        env = os.environ.copy()
        env["HOME"] = str(home)
        return subprocess.run(
            [sys.executable, str(INSTALLER), *args],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_preview_is_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            result = self.run_installer(home=home)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Preview only", result.stdout)
            self.assertFalse((home / ".local/share/termax").exists())
            self.assertFalse((home / ".local/bin/tx").exists())

    def test_apply_is_refused_without_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            result = self.run_installer("--apply", home=home)
            self.assertEqual(result.returncode, 2)
            self.assertIn("REFUSED", result.stdout)
            self.assertFalse((home / ".local/share/termax").exists())
            self.assertFalse((home / ".local/bin/tx").exists())

    def test_existing_install_is_not_modified(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            app = home / ".local/share/termax"
            app.mkdir(parents=True)
            (app / "VERSION").write_text("0.1.0", encoding="utf-8")
            sentinel = app / "preserve-me.txt"
            sentinel.write_text("baseline", encoding="utf-8")
            result = self.run_installer("--apply", home=home)
            self.assertEqual(result.returncode, 2)
            self.assertEqual((app / "VERSION").read_text(encoding="utf-8"), "0.1.0")
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "baseline")
            self.assertFalse((home / ".local/bin/tx").exists())

    def test_help_is_available(self):
        result = subprocess.run(
            [sys.executable, str(INSTALLER), "--help"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--apply", result.stdout)


if __name__ == "__main__":
    unittest.main()
