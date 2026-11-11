"""Sixel output helpers. No mandatory Python imaging dependencies."""
import shutil
import subprocess
import sys
from pathlib import Path

from .capabilities import probe


def _encode(path, width=None, height=None):
    chafa = shutil.which("chafa")
    if chafa:
        cmd = [chafa, "--format=sixels"]
        if width or height:
            cmd += ["--size", f"{width or 40}x{height or 20}"]
        cmd.append(str(path))
    else:
        img2sixel = shutil.which("img2sixel")
        if not img2sixel:
            raise RuntimeError("Install Chafa or libsixel: pkg install chafa libsixel")
        cmd = [img2sixel]
        if width:
            cmd += ["-w", str(int(width))]
        if height:
            cmd += ["-h", str(int(height))]
        cmd.append(str(path))
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
    if result.returncode or not result.stdout:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise RuntimeError(detail or "Sixel encoder returned no image data")
    return result.stdout


def display(image, width=40, height=20, force=False):
    """Encode and write an image as Sixel. force bypasses only the opt-in guard."""
    status = probe()
    if not sys.stdout.isatty():
        raise RuntimeError("Sixel output requires an interactive terminal")
    if not force and status["display_supported"] is not True:
        raise RuntimeError(
            "Sixel display is not verified. Run 'termax graphics demo'; "
            "if it renders, set TERMAX_SIXEL=1 in your shell."
        )
    data = _encode(Path(image).expanduser(), width, height)
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()
    return True


def _test_sixel():
    # A dependency-free Sixel test image: three coloured horizontal bands.
    esc = "\x1b"
    parts = [esc + "Pq", "#1;2;100;0;0", "#2;2;0;100;0", "#3;2;0;0;100"]
    for colour in ("#1", "#2", "#3"):
        parts.extend((colour, "~" * 24))
        if colour != "#3":
            parts.append("-")
    parts.append(esc + "\\")
    return "".join(parts).encode("ascii")


def demo():
    if not sys.stdout.isatty():
        raise RuntimeError("Sixel demo requires an interactive terminal")
    sys.stdout.buffer.write(_test_sixel())
    sys.stdout.buffer.flush()
    return True
