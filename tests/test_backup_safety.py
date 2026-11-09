from __future__ import annotations

import importlib.util
import io
import json
import os
import tarfile
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "termax" / "backup.py"
SPEC = importlib.util.spec_from_file_location("termax_backup", MODULE)
assert SPEC and SPEC.loader
backup = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(backup)


class BackupSafetyTests(unittest.TestCase):
    def test_rejects_traversal_and_secret_paths(self):
        for path in ("../outside", "/etc/passwd", ".ssh/id_ed25519", ".config/../x"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                backup.safe_path(path)

    def test_rejects_symlinked_parent(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "home"
            outside = Path(tmp) / "outside"
            home.mkdir()
            outside.mkdir()
            (home / ".config").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlinked parent"):
                backup.checked_destination(home, ".config/starship.toml")

    def test_rejects_symlink_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            target = home / "real"
            target.write_text("safe")
            (home / ".zshrc").symlink_to(target)
            with self.assertRaisesRegex(ValueError, "symlink destination"):
                backup.checked_destination(home, ".zshrc")

    def test_load_valid_archive_and_verify_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "backup.tar.gz"
            data = b"test config"
            manifest = {"schema": 1, "files": [{
                "path": ".zshrc", "sha256": backup.digest(data),
                "size": len(data), "mode": 0o600,
            }]}
            with tarfile.open(archive, "w:gz") as tf:
                raw = json.dumps(manifest).encode()
                info = tarfile.TarInfo("manifest.json")
                info.size = len(raw)
                tf.addfile(info, io.BytesIO(raw))
                info = tarfile.TarInfo("payload/.zshrc")
                info.size = len(data)
                tf.addfile(info, io.BytesIO(data))
            self.assertEqual(backup.load(archive)[".zshrc"][0], data)

    def test_unique_paths_do_not_collide(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = backup.unique_path(Path(tmp), "backup-", ".tar.gz")
            second = backup.unique_path(Path(tmp), "backup-", ".tar.gz")
            self.assertNotEqual(first, second)
            self.assertTrue(first.exists())
            self.assertTrue(second.exists())


if __name__ == "__main__":
    unittest.main()
