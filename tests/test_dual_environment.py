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


    def test_bootstrap_preserves_existing_user_zsh_plugins(self):
        for path in ("termax/bootstrap.sh", "termax/proot-bootstrap.sh"):
            script = (ROOT / path).read_text(encoding="utf-8")
            self.assertIn("managed_plugins =", script)
            self.assertIn("existing_plugins + managed_plugins", script)
            self.assertIn("dict.fromkeys", script)

    def test_zsh_backup_names_do_not_collide_within_one_second(self):
        for path in ("termax/bootstrap.sh", "termax/proot-bootstrap.sh"):
            script = (ROOT / path).read_text(encoding="utf-8")
            self.assertIn("time.time_ns()", script)

    def test_debian_python_environment_is_separate_from_ww(self):
        proot = (ROOT / "termax/proot-bootstrap.sh").read_text(encoding="utf-8")
        self.assertIn('$HOME/.local/share/termax/venv', proot)
        self.assertNotIn('ww/.venv', proot)
        self.assertIn("WW's existing repository, virtualenv and cookies were not modified.", proot)


if __name__ == "__main__":
    unittest.main()
