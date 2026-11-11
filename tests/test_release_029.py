import io, json, tarfile, tempfile, unittest
from pathlib import Path
from termax.backup import safe_path, load, safe_destination
from termax.browser import transfer
class Release029Tests(unittest.TestCase):
 def test_allowlist(self):
  self.assertEqual(str(safe_path(".zshrc")),".zshrc")
  with self.assertRaises(ValueError): safe_path(".bashrc")
  with self.assertRaises(ValueError): safe_path("../.ssh/id_ed25519")
 def test_symlink_parent(self):
  with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as outside:
   h=Path(home); (h/".config").symlink_to(outside)
   with self.assertRaises(ValueError): safe_destination(h,".config/starship.toml")
 def test_archive_rejects_unlisted_path(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"bad.tar.gz"; raw=json.dumps({"schema":1,"files":[{"path":".bashrc","size":1,"sha256":"x","mode":384}]}).encode()
   with tarfile.open(p,"w:gz") as tf:
    m=tarfile.TarInfo("manifest.json"); m.size=len(raw); tf.addfile(m,io.BytesIO(raw))
    m=tarfile.TarInfo("payload/.bashrc"); m.size=1; tf.addfile(m,io.BytesIO(b"x"))
   with self.assertRaises(ValueError): load(p)
 def test_copy_collision_and_symlink(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d); src=r/"a"; src.write_text("ok"); dst=r/"dest"; dst.mkdir()
   transfer([src],dst)
   with self.assertRaises(FileExistsError): transfer([src],dst)
   link=r/"link"; link.symlink_to(src)
   with self.assertRaises(ValueError): transfer([link],dst)
 def test_prevent_directory_into_itself(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d); src=r/"folder"; src.mkdir(); dst=src/"inside"; dst.mkdir()
   with self.assertRaises(ValueError): transfer([src],dst)
if __name__=="__main__": unittest.main()

# CI exercises this module on each supported Python version.
