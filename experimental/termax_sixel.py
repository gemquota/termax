"""SIXEL image renderer for TERMAX Explorer.

SIXEL output is opt-in because emitting graphics escapes to an unsupported
terminal can leave garbage on screen. Set TERMAX_SIXEL=1 or use --sixel.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def render_sixel(path: Path, *, width: int = 80, height: int = 24) -> bool:
    """Render an image as SIXEL; return False when no usable encoder exists."""
    if not sys.stdout.isatty():
        return False

    chafa = shutil.which("chafa")
    if chafa and path.suffix.lower() not in {".gif"}:
        result = subprocess.run(
            [chafa, "--format=sixels", "--probe=off", "--relative=off",
             "--size", f"{max(8, width)}x{max(4, height)}", str(path)],
            check=False,
        )
        if result.returncode == 0:
            return True

    img2sixel = shutil.which("img2sixel")
    if img2sixel:
        args = [img2sixel]
        if path.suffix.lower() == ".gif":
            args.append("--static")
        result = subprocess.run([*args, str(path)], check=False)
        return result.returncode == 0

    return False
