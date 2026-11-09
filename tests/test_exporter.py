from __future__ import annotations

import hashlib
import importlib.util
import tarfile
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools/export-installed-core.py"
SPEC = importlib.util.spec_from_file_location("termax_exporter", MODULE_PATH)
assert SPEC and SPEC.loader
EXPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXPORTER)


class ExporterTests(unittest.TestCase):
    def make_source(self, root: Path) -> Path:
        source = root / "termax"
        files = {
            "VERSION": "0.1.0\n",
            "termax/cli.py": "print('cli')\n",
            "termax/registry.py": "COMMANDS = ()\n",
            "termax/backup.py": "def backup(): pass\n",
            "config/plugins.json": '{"schema": 1}\n',
            "termax/__pycache__/cache.pyc": "not source",
            "backups/private.tar.gz": "not source",
            "config/hosts.yml": "token: never-export",
        }
        for rel, value in files.items():
            path = source / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(value, encoding="utf-8")
        return source

    def test_export_contains_source_and_excludes_cache_backup_and_credentials(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_source(root)
            output = root / "out.tar.gz"
            count, digest = EXPORTER.export(source, output)
            self.assertGreater(count, 0)
            self.assertEqual(digest, hashlib.sha256(output.read_bytes()).hexdigest())
            with tarfile.open(output, "r:gz") as archive:
                names = set(archive.getnames())
            self.assertIn("VERSION", names)
            self.assertIn("termax/cli.py", names)
            self.assertIn("config/plugins.json", names)
            self.assertFalse(any("__pycache__" in name for name in names))
            self.assertFalse(any("backups/" in name for name in names))
            self.assertNotIn("config/hosts.yml", names)

    def test_export_refuses_incomplete_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "incomplete"
            source.mkdir()
            with self.assertRaises(ValueError):
                EXPORTER.export(source, root / "out.tar.gz")


if __name__ == "__main__":
    unittest.main()
