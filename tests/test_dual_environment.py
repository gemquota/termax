import re
import subprocess
import sys
import tempfile
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

    def test_both_bootstrap_scripts_install_powerlevel10k_and_plugins(self):
        native = (ROOT / "termax/bootstrap.sh").read_text(encoding="utf-8")
        proot = (ROOT / "termax/proot-bootstrap.sh").read_text(encoding="utf-8")
        for script in (native, proot):
            self.assertIn("powerlevel10k.git", script)
            self.assertIn("p10k-lean.zsh", script)
            self.assertIn("zsh-autocomplete", script)
            self.assertIn("zsh-history-substring-search", script)

    def test_bootstraps_preserve_user_plugins_and_theme(self):
        fixture = (
            'export ZSH="$HOME/.oh-my-zsh"\n'
            'ZSH_THEME="agnoster"\n'
            'plugins=(git docker kubectl)\n'
            'source "$ZSH/oh-my-zsh.sh"\n'
        )
        for relative in ("termax/bootstrap.sh", "termax/proot-bootstrap.sh"):
            script = (ROOT / relative).read_text(encoding="utf-8")
            match = re.search(r"python(?:3)? - \"\$ZRC\" <<'PY'\n(.*?)\nPY", script, re.S)
            self.assertIsNotNone(match, relative)
            with tempfile.TemporaryDirectory() as directory:
                zshrc = Path(directory) / ".zshrc"
                zshrc.write_text(fixture, encoding="utf-8")
                result = subprocess.run(
                    [sys.executable, "-c", match.group(1), str(zshrc)],
                    text=True, capture_output=True, check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                updated = zshrc.read_text(encoding="utf-8")
                self.assertIn('plugins=(git docker kubectl)', updated)
                self.assertIn('plugins+=(zsh-autosuggestions zsh-syntax-highlighting zsh-autocomplete zsh-history-substring-search colored-man-pages)', updated)
                self.assertIn('ZSH_THEME="agnoster"', updated)
                self.assertEqual(updated.count("TERMAX_MANAGED_PLUGINS"), 1)
                self.assertEqual(updated.count("zsh-autosuggestions"), 1)

    def test_default_oh_my_zsh_theme_switches_to_powerlevel10k(self):
        fixture = (
            'export ZSH="$HOME/.oh-my-zsh"\n'
            'ZSH_THEME="robbyrussell"\n'
            'plugins=(git zsh-autosuggestions)\n'
            'source "$ZSH/oh-my-zsh.sh"\n'
        )
        for relative in ("termax/bootstrap.sh", "termax/proot-bootstrap.sh"):
            script = (ROOT / relative).read_text(encoding="utf-8")
            match = re.search(r"python(?:3)? - \"\\$ZRC\" <<'PY'\\n(.*?)\\nPY", script, re.S)
            self.assertIsNotNone(match, relative)
            with tempfile.TemporaryDirectory() as directory:
                zshrc = Path(directory) / ".zshrc"
                zshrc.write_text(fixture, encoding="utf-8")
                result = subprocess.run(
                    [sys.executable, "-c", match.group(1), str(zshrc)],
                    text=True, capture_output=True, check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                updated = zshrc.read_text(encoding="utf-8")
                self.assertIn('ZSH_THEME="powerlevel10k/powerlevel10k"', updated)
                self.assertIn('plugins=("${(@u)plugins}")', updated)
                self.assertIn('plugins=(git zsh-autosuggestions)', updated)

    def test_debian_audit_variables_are_defined_before_any_audit(self):
        proot = (ROOT / "termax/proot-bootstrap.sh").read_text(encoding="utf-8")
        self.assertLess(proot.index('CUSTOM="${ZSH_CUSTOM:-'), proot.index('if [[ "$MODE" == "check" ]]'))
        self.assertLess(proot.index('VENV="$HOME/.local/share/termax/venv"'), proot.index('if [[ "$MODE" == "check" ]]'))

    def test_debian_final_audit_runs_after_installation(self):
        proot = (ROOT / "termax/proot-bootstrap.sh").read_text(encoding="utf-8")
        self.assertGreater(proot.rindex("FINAL_MISSING=()"), proot.index("Installing/configuring Debian Zsh"))
        self.assertIn('zsh -n "$HOME/.zshrc"', proot)

    def test_debian_check_does_not_create_a_log_or_mutate_packages(self):
        proot = (ROOT / "termax/proot-bootstrap.sh").read_text(encoding="utf-8")
        self.assertIn('if [[ "$MODE" != "check" ]]; then exec > >(tee -a "$LOG") 2>&1; fi', proot)
        check = proot.split('if [[ "$MODE" == "check" ]]; then', 1)[1].split("\nfi", 1)[0]
        self.assertNotIn("apt-get install", check)
        self.assertNotIn("apt-get update", check)

    def test_host_binds_source_tree_into_debian_instead_of_using_host_path(self):
        native = (ROOT / "termax/bootstrap.sh").read_text(encoding="utf-8")
        lifecycle = (ROOT / "termax/commands/lifecycle.py").read_text(encoding="utf-8")
        self.assertIn('--bind "$APP_ROOT:/mnt/termax-source"', native)
        self.assertIn('f"{ROOT}:/mnt/termax-source"', lifecycle)
        self.assertIn('/mnt/termax-source/termax/proot-bootstrap.sh', native)
        self.assertIn('/mnt/termax-source/termax/proot-bootstrap.sh', lifecycle)

    def test_python_audit_covers_all_declared_requirements(self):
        system = (ROOT / "termax/system.py").read_text(encoding="utf-8")
        required = ("cloudscraper", "fastapi", "httplib2", "opentelemetry",
                    "requests_toolbelt", "uvicorn", "textual", "prompt_toolkit",
                    "plotext", "networkx", "yaml", "typer")
        for module in required:
            self.assertIn(f'"{module}"', system)

    def test_debian_python_environment_is_separate_from_ww(self):
        proot = (ROOT / "termax/proot-bootstrap.sh").read_text(encoding="utf-8")
        self.assertIn('$HOME/.local/share/termax/venv', proot)
        self.assertNotIn('ww/.venv', proot)
        self.assertIn("WW's existing repository, virtualenv and cookies were not modified.", proot)


if __name__ == "__main__":
    unittest.main()
