import io
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from termax.commands import lifecycle

class LifecyclePreflightTests(unittest.TestCase):
    def test_up_check_is_read_only_and_reports_action_plan(self):
        probe = {
            "platform": "Android-test", "machine": "aarch64", "python": "3.13",
            "shell": "bash", "commands": {"git": "/usr/bin/git"},
            "modules": {"rich": False, "yaml": True},
        }
        with tempfile.TemporaryDirectory() as temp:
            with (
                mock.patch.object(lifecycle, "_is_termux", return_value=True),
                mock.patch.object(lifecycle, "probe", return_value=probe),
                mock.patch.object(lifecycle, "_manifest", side_effect=[["git"], ["rich"], ["zsh"]]),
                mock.patch.object(lifecycle, "_package_state", return_value=True),
                mock.patch.object(lifecycle, "_zsh_audit", return_value={"Oh My Zsh": True}),
                mock.patch.object(lifecycle, "_write_report") as report,
                mock.patch.object(lifecycle, "_run") as run,
                mock.patch.object(Path, "home", return_value=Path(temp)),
            ):
                result = lifecycle.up(SimpleNamespace(check=True, debug=False))
        self.assertEqual(result, 0)
        run.assert_not_called()
        report.assert_called_once()
        self.assertIn("PROPOSED ACTION PLAN", report.call_args.args[0])
        self.assertIn("Missing modules: rich", report.call_args.args[0])

    def test_report_never_overwrites_existing_default(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            default = home / "termax-report.txt"
            default.write_text("keep me", encoding="utf-8")
            with (
                mock.patch.object(Path, "home", return_value=home),
                mock.patch.object(lifecycle.sys, "stdin", new=io.StringIO()),
                mock.patch.object(lifecycle.time, "strftime", return_value="20261112-123456"),
            ):
                lifecycle._write_report(["new report"])
            self.assertEqual(default.read_text(encoding="utf-8"), "keep me")
            dated = home / "termax-report-20261112-123456.txt"
            self.assertEqual(dated.read_text(encoding="utf-8"), "new report\n")

if __name__ == "__main__":
    unittest.main()
