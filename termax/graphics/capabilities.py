"""Conservative graphics capability checks.

Termux:Monet contains a Sixel parser/renderer, but Termux exposes the same
TERM/PREFIX values across emulator builds. Therefore we never infer display
support from TERM, COLORTERM, Chafa, or libsixel being installed.
"""
import os
import shutil
import sys


def probe():
    prefix = os.environ.get("PREFIX", "")
    is_termux = prefix.endswith("/com.termux/files/usr")
    encoder = shutil.which("chafa") or shutil.which("img2sixel")
    override = os.environ.get("TERMAX_SIXEL", "auto").strip().lower()
    if override in {"1", "true", "yes", "on"}:
        display = True
        method = "user-confirmed"
    elif override in {"0", "false", "no", "off"}:
        display = False
        method = "disabled-by-user"
    else:
        display = None
        method = "not-verified"
    return {
        "is_termux": is_termux,
        "prefix": prefix or None,
        "term": os.environ.get("TERM"),
        "colorterm": os.environ.get("COLORTERM"),
        "encoder": "chafa" if shutil.which("chafa") else (
            "img2sixel" if shutil.which("img2sixel") else None
        ),
        "encoder_path": encoder,
        "stdout_is_tty": sys.stdout.isatty(),
        "display_supported": display,
        "display_verification": method,
        "ready": bool(encoder and sys.stdout.isatty() and display is True),
        "note": (
            "Run 'termax graphics demo' and set TERMAX_SIXEL=1 only after "
            "you can see the test pattern. TERM and truecolor do not prove Sixel."
        ),
    }


def supported():
    """Return True/False when explicitly configured, otherwise None (unknown)."""
    return probe()["display_supported"]
