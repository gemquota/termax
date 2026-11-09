#!/usr/bin/env python3
"""Run a non-interactive command and visualize its output activity."""
from __future__ import annotations

import argparse
import math
import shutil
import subprocess
import sys
import time

RESET = "\x1b[0m"
COLORS = {"ok":"\x1b[32m", "warn":"\x1b[33m", "bad":"\x1b[31m", "info":"\x1b[36m", "run":"\x1b[35m"}


def classify(line: str) -> str:
    s = line.lower()
    if any(x in s for x in ("traceback", "error", "failed", "fatal", "exception")):
        return "bad"
    if any(x in s for x in ("warning", "deprecated", "warn")):
        return "warn"
    if any(x in s for x in ("passed", "success", "complete", "done", "✓")):
        return "ok"
    if any(x in s for x in ("test", "collecting", "building", "installing")):
        return "info"
    return "run"


def waveform(seed: int, width: int) -> str:
    glyphs = "▁▂▃▄▅▆▇█"
    out = []
    for i in range(max(8, min(width, 56))):
        v = abs(math.sin((seed * .17) + (i * .71)) * math.cos((seed * .09) - i * .13))
        out.append(glyphs[min(7, int(v * 8))])
    return "".join(out)


def main(argv=None):
    parser = argparse.ArgumentParser(description="TERMAX reactive terminal output visualizer")
    parser.add_argument("--aquarium", action="store_true",
                        help="show a reactive ASCII reef whose state responds to output")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="command to execute after --")
    args = parser.parse_args(argv)
    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("provide a command, e.g. tx pulse -- python -m unittest")
    interactive = sys.stdout.isatty()
    reef = None
    if args.aquarium:
        try:
            from termax_aquarium import Aquarium
            reef = Aquarium()
        except ImportError:
            print("Aquarium sidecar unavailable; using waveform mode.", file=sys.stderr)
    started = time.monotonic()
    count = 0
    errors = 0
    try:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, errors="replace", bufsize=1)
    except OSError as exc:
        print(f"TERMAX pulse: cannot start command: {exc}", file=sys.stderr)
        return 127
    assert proc.stdout is not None
    try:
        for raw in proc.stdout:
            line = raw.rstrip("\n")
            kind = classify(line)
            count += 1
            errors += kind == "bad"
            # Preserve command output; the visual layer is an additional signal.
            print(raw, end="", flush=True)
            if interactive:
                if reef is not None:
                    print(reef.render(kind), flush=True)
                else:
                    width = shutil.get_terminal_size((80, 24)).columns - 18
                    color = COLORS[kind]
                    print(f"{color}  ◉ {kind.upper():4} {waveform(count + len(line), width)}{RESET}", flush=True)
        code = proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        try:
            code = proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            code = proc.wait()
    elapsed = time.monotonic() - started
    if interactive:
        state = "OK" if code == 0 else "EXIT " + str(code)
        color = COLORS["ok"] if code == 0 else COLORS["bad"]
        print(f"{color} TERMAX PULSE  {state}  ·  {count} lines  ·  {errors} error-like lines  ·  {elapsed:.1f}s{RESET}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
