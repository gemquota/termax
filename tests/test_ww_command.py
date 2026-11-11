import argparse
import unittest
from unittest.mock import patch

from termax.commands.ww import ask


class WWCommandTests(unittest.TestCase):
    @patch("termax.commands.ww.subprocess.run")
    @patch("termax.commands.ww.shutil.which", return_value="/usr/bin/proot-distro")
    def test_forwards_prompt_to_existing_proot_install(self, _which, run):
        run.return_value.returncode = 0
        result = ask(argparse.Namespace(prompt=["Explain", "this", "error"]))

        self.assertEqual(result, 0)
        command = run.call_args.args[0]
        self.assertEqual(command[:4], ["proot-distro", "login", "debian", "--"])
        self.assertIn("--noprofile", command)
        self.assertIn("--norc", command)
        self.assertEqual(command[-1], "Explain this error")

    @patch("termax.commands.ww.shutil.which", return_value=None)
    def test_reports_missing_proot_distro(self, _which):
        result = ask(argparse.Namespace(prompt=["hello"]))
        self.assertEqual(result, 2)

    def test_requires_a_prompt(self):
        result = ask(argparse.Namespace(prompt=[]))
        self.assertEqual(result, 2)


if __name__ == "__main__":
    unittest.main()
