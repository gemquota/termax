"""Bridge TERMAX's native Termux CLI to the existing WW install in Debian proot."""
from __future__ import annotations
import shutil
import subprocess
import sys

WW_ROOT = "/data/data/com.termux/files/home/ww"
WW_SCRIPT = 'cd /data/data/com.termux/files/home/ww && exec .venv/bin/python gemini_bridge.py --prompt "$1" --no-banner'

def ask(args) -> int:
    prompt = " ".join(args.prompt).strip()
    if not prompt:
        print('Usage: tx ask "your prompt"', file=sys.stderr)
        return 2
    if shutil.which("proot-distro") is None:
        print("WW backend unavailable: install proot-distro in native Termux.", file=sys.stderr)
        return 2
    command = ["proot-distro","login","debian","--","/bin/bash","--noprofile","--norc","-c",WW_SCRIPT,"termax-ww",prompt]
    try:
        return subprocess.run(command,check=False).returncode
    except OSError as exc:
        print(f"Could not launch WW: {exc}",file=sys.stderr)
        return 1
