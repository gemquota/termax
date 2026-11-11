import os, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; INSTALLER=ROOT/"install.py"
class InstallerTests(unittest.TestCase):
 def run_it(self,*args,home):
  env=os.environ.copy(); env["HOME"]=str(home)
  return subprocess.run([sys.executable,str(INSTALLER),*args],cwd=ROOT,env=env,text=True,capture_output=True)
 def test_preview_read_only(self):
  with tempfile.TemporaryDirectory() as d:
   h=Path(d); r=self.run_it(home=h); self.assertEqual(r.returncode,0,r.stderr)
   self.assertFalse((h/".local/share/termax").exists())
 def test_apply_installs_both_launchers(self):
  with tempfile.TemporaryDirectory() as d:
   h=Path(d); r=self.run_it("--apply",home=h); self.assertEqual(r.returncode,0,r.stderr)
   self.assertEqual((h/".local/share/termax/VERSION").read_text().strip(),"0.2.9")
   self.assertTrue((h/".local/bin/termax").exists()); self.assertTrue((h/".local/bin/tx").exists())
 def test_upgrade_preserves_backup(self):
  with tempfile.TemporaryDirectory() as d:
   h=Path(d); app=h/".local/share/termax"; app.mkdir(parents=True); (app/"VERSION").write_text("0.1.0")
   r=self.run_it("--apply",home=h); self.assertEqual(r.returncode,0,r.stderr)
   self.assertTrue(list((h/".local/share").glob("termax.backup-*")))
 def test_help(self):
  r=subprocess.run([sys.executable,str(INSTALLER),"--help"],cwd=ROOT,text=True,capture_output=True)
  self.assertEqual(r.returncode,0); self.assertIn("--apply",r.stdout)
if __name__=="__main__": unittest.main()
