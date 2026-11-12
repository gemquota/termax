import unittest
from termax.cli import COMMANDS, _parser

class CommandAliasTests(unittest.TestCase):
    def test_every_command_has_a_distinct_alias(self):
        names = [name for name, _, _ in COMMANDS]
        aliases = [alias for _, alias, _ in COMMANDS]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(aliases), len(set(aliases)))
        self.assertFalse(set(names) & set(aliases))

    def test_full_and_short_names_parse(self):
        parser = _parser()
        for name, alias, _ in COMMANDS:
            with self.subTest(command=name):
                full = parser.parse_args([name] + (["sample.tar.gz"] if name == "load" else []))
                short = parser.parse_args([alias] + (["sample.tar.gz"] if name == "load" else []))
                self.assertEqual(full.command, name)
                self.assertEqual(short.command, alias)

    def test_retired_diagnostics_are_not_public_commands(self):
        parser = _parser()
        public = {name for name, _, _ in COMMANDS} | {alias for _, alias, _ in COMMANDS}
        for retired in ("doctor", "status", "dashboard", "audit", "repair", "nexus-legacy"):
            self.assertNotIn(retired, public)

if __name__ == "__main__":
    unittest.main()
