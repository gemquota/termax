import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class DualEnvironmentBootstrapTests(unittest.TestCase):
    def test_native_manifest_installs_proot_distro(self):
        packages = (ROOT / "config/termux-packages.txt").read_text(encoding="utf-8")
        self.assertIn("proot-distro", packages.splitlines())

    def test_both_manifests_include_the_zsh_stack(self):
        native = set((ROOT / "config/termux-packages.txt").read_text(encoding="utf-8").splitlines())
        debian = set((ROOT / "config/debian-packages.txt").read_text(encoding="utf-8").splitlines())
        self.assertIn("zsh", native)
        self.assertIn("zsh", debian)
        self.assertIn("zsh-autosuggestions", debian)
        self.assertIn("zsh-syntax-highlighting", debian)

    def test_both_bootstrap_scripts_install_powerlevel10k(self):
        native = (ROOT / "termax/bootstrap.sh").read_text(encoding="utf-8")
        proot = (ROOT / "termax/proot-bootstrap.sh").read_text(encoding="utf-8")
        for script in (native, proot):
            self.assertIn("powerlevel10k.git", script)
            self.assertIn("p10k-lean.zsh", script)
            self.assertIn("zsh-autocomplete", script)
            self.assertIn("zsh-history-substring-search", script)

    def test_debian_python_environment_is_separate_from_ww(self):
        proot = (ROOT / "termax/proot-bootstrap.sh").read_text(encoding="utf-8")
        self.assertIn("$HOME/.local/share/termax/venv", proot)
        self.assertNotIn("ww/.venv", proot)

if __name__ == "__main__":
    unittest.main()
