import os
import unittest
from unittest.mock import patch
from termax.graphics.capabilities import probe, supported
from termax.graphics.renderer import _test_sixel


class SixelCapabilityTests(unittest.TestCase):
    def test_unknown_is_not_guessed_from_term(self):
        with patch.dict(os.environ, {"TERM": "xterm-256color", "COLORTERM": "truecolor"}, clear=True):
            self.assertIsNone(supported())

    def test_explicit_user_confirmation(self):
        with patch.dict(os.environ, {"TERMAX_SIXEL": "1"}, clear=True):
            self.assertTrue(supported())
            self.assertEqual(probe()["display_verification"], "user-confirmed")

    def test_explicit_disable(self):
        with patch.dict(os.environ, {"TERMAX_SIXEL": "0"}, clear=True):
            self.assertFalse(supported())

    def test_demo_is_sixel_dcs(self):
        data = _test_sixel()
        self.assertTrue(data.startswith(b"\x1bPq"))
        self.assertTrue(data.endswith(b"\x1b\\"))
        self.assertIn(b"#1;2;100;0;0", data)


if __name__ == "__main__":
    unittest.main()
