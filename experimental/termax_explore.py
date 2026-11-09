#!/usr/bin/env python3
"""Experimental, dependency-free TERMAX visual filesystem navigator.

Keys: arrows/jk move, Enter open, Backspace go up, / filter, . hidden,
p preview, o editor, n new folder, r rename, c copy, m move, d send to trash, q quit.
Destructive deletion is deliberately replaced with a reversible trash move.
"""
from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess
import sys
import termios
import tty
from pathlib import Path

RESET = "\x1b[0m"
CYAN = "\x1b[36m"
DIM = "\x1b[2m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
RED = "\x1b[31m"


def human_size(n: int) -> str:
    value = float(n)
    for unit in ("B", "K", "M", "G", "T"):
        if value < 1024 or unit == "T":
            return f"{value:.0f}{unit}" if unit == "B" else f"{value:.1f}{unit}"
        value /= 1024
    return f"{n}B"


class Explorer:
    def __init__(self, start: Path):
        self.cwd = start.expanduser().resolve()
        self.entries: list[Path] = []
        self.index = 0
        self.hidden = False
        self.query = ""
        self.preview = False
        self.sixel = False
        self.message = "Enter open | / filter | . hidden | p preview | v SIXEL preview | o editor | n new | r rename | c copy | m move | d trash | q quit"
        self.refresh()

    def refresh(self):
        try:
            items = list(os.scandir(self.cwd))
        except OSError as exc:
            self.message = f"Cannot read directory: {exc}"
            items = []
        items.sort(key=lambda e: (not e.is_dir(follow_symlinks=False), e.name.casefold()))
        self.entries = [
            Path(item.path) for item in items
            if (self.hidden or not item.name.startswith("."))
            and self.query.casefold() in item.name.casefold()
        ]
        self.index = min(self.index, max(0, len(self.entries) - 1))

    @property
    def selected(self) -> Path | None:
        return self.entries[self.index] if self.entries else None

    def prompt(self, label: str) -> str:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.original)
        try:
            print(f"\r\n{label}: ", end="", flush=True)
            return input()
        finally:
            tty.setraw(sys.stdin.fileno())

    def render(self):
        width, height = shutil.get_terminal_size((80, 24))
        body = max(5, height - 7)
        print("\x1b[2J\x1b[H", end="")
        print(f"{CYAN} TERMAX / EXPLORER {RESET} {DIM}experimental filesystem cockpit{RESET}")
        print(f"{GREEN}{self.cwd}{RESET}")
        print("─" * max(20, width))
        start = max(0, min(self.index - body // 2, len(self.entries) - body))
        for row, path in enumerate(self.entries[start:start + body], start):
            try:
                info = path.lstat()
                is_dir = stat.S_ISDIR(info.st_mode)
                is_link = stat.S_ISLNK(info.st_mode)
                icon = "▸" if is_dir else ("↗" if is_link else "·")
                size = "<DIR>" if is_dir else human_size(info.st_size)
            except OSError:
                icon, size = "?", "?"
            marker = "▶" if row == self.index else " "
            tint = CYAN if row == self.index else (YELLOW if icon == "▸" else RESET)
            print(f"{marker} {tint}{icon} {path.name[:max(8,width-22)]:<{max(8,width-22)}}{RESET} {DIM}{size:>7}{RESET}")
        if self.preview and self.selected:
            print("─" * max(20, width))
            self.show_preview(self.selected, min(5, height // 4))
        print("─" * max(20, width))
        print(f"{DIM}{len(self.entries)} entries | hidden={'on' if self.hidden else 'off'} | filter={self.query or 'none'}{RESET}")
        print(self.message[:width])

    def show_preview(self, path: Path, lines: int):
        if path.is_dir():
            try:
                children = sorted(p.name for p in path.iterdir())[:lines]
                print(f"{CYAN}Directory preview:{RESET} " + "  ".join(children))
            except OSError as exc:
                print(f"{RED}{exc}{RESET}")
            return
        try:
            width = max(20, shutil.get_terminal_size((80, 24)).columns - 2)
            image_exts = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
            if path.suffix.lower() in image_exts and self.sixel:
                from termax_sixel import render_sixel
                if render_sixel(path, width=width, height=max(8, lines * 3)):
                    return
                print(f"{YELLOW}SIXEL renderer unavailable; falling back to character preview.{RESET}")
            if path.suffix.lower() in image_exts and shutil.which("chafa"):
                subprocess.run(["chafa", "--format=symbols", "--size", f"{width}x{max(3, lines)}", str(path)], check=False)
                return
            if shutil.which("bat"):
                result = subprocess.run(
                    ["bat", "--color=always", "--style=plain", "--paging=never",
                     "--line-range", f"1:{max(3, lines)}", str(path)],
                    capture_output=True, text=True, errors="replace"
                )
                if result.returncode == 0:
                    print(result.stdout, end="")
                    return
            data = path.read_bytes()
            if b"\0" in data[:4096]:
                print(f"{DIM}Binary file · {human_size(len(data))}{RESET}")
                return
            text = data.decode("utf-8", "replace").splitlines()
            for line in text[:lines]:
                print(DIM + line[:width] + RESET)
        except OSError as exc:
            print(f"{RED}Preview unavailable: {exc}{RESET}")

    def target_path(self, value: str) -> Path:
        candidate = Path(value).expanduser()
        return (self.cwd / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()

    def open_editor(self, item: Path):
        editor = os.environ.get("VISUAL") or os.environ.get("EDITOR")
        editor = editor or next((name for name in ("nvim", "vim", "vi", "nano") if shutil.which(name)), "")
        executable = shutil.which(editor) if editor else None
        if not executable:
            self.message = "No editor found. Set EDITOR or VISUAL."
            return
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.original)
        try:
            subprocess.call([executable, str(item)])
        finally:
            tty.setraw(sys.stdin.fileno())

    def operate(self, key: str):
        item = self.selected
        if key == "." :
            self.hidden = not self.hidden
            self.refresh()
        elif key == "/":
            self.query = self.prompt("Filter (empty clears)")
            self.index = 0
            self.refresh()
        elif key == "p":
            self.preview = not self.preview
        elif key == "v":
            self.sixel = not self.sixel
            self.preview = True
            self.message = f"SIXEL preview {'enabled' if self.sixel else 'disabled'} (requires a SIXEL-capable terminal)"
        elif key == "o" and item and item.is_file() and not item.is_symlink():
            self.open_editor(item)
        elif key == "n":
            name = self.prompt("New directory name").strip()
            if name:
                dest = self.target_path(name)
                if dest.exists():
                    self.message = "That path already exists."
                else:
                    dest.mkdir(parents=False)
                    self.message = f"Created {dest.name}"
                    self.refresh()
        elif key == "r" and item:
            name = self.prompt("Rename to").strip()
            if name and Path(name).name == name:
                dest = item.with_name(name)
                if not dest.exists():
                    item.rename(dest)
                    self.message = f"Renamed to {name}"
                    self.refresh()
                else:
                    self.message = "Destination already exists."
        elif key in ("c", "m") and item:
            raw = self.prompt("Copy to" if key == "c" else "Move to").strip()
            if raw:
                dest = self.target_path(raw)
                if dest.exists() and dest.is_dir():
                    dest = dest / item.name
                if dest.exists():
                    self.message = "Destination already exists."
                elif item.is_symlink():
                    self.message = "Refusing to copy/move a symlink."
                elif key == "c":
                    shutil.copytree(item, dest, symlinks=True) if item.is_dir() else shutil.copy2(item, dest)
                    self.message = f"Copied {item.name}"
                else:
                    shutil.move(str(item), str(dest))
                    self.message = f"Moved {item.name}"
                    self.refresh()
        elif key == "d" and item:
            answer = self.prompt(f"Move {item.name} to TERMAX trash? [y/N]").strip().lower()
            if answer == "y":
                trash = Path.home() / ".local/share/Trash/files"
                if trash.is_symlink():
                    self.message = "Refusing symlinked trash directory."
                    return
                trash.mkdir(parents=True, exist_ok=True)
                dest = trash / item.name
                suffix = 0
                while dest.exists():
                    suffix += 1
                    dest = trash / f"{item.name}.tx-{os.getpid()}-{suffix}"
                shutil.move(str(item), str(dest))
                self.message = f"Moved to trash: {dest}"
                self.refresh()

    def run(self):
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            print("TERMAX Explorer needs an interactive terminal.")
            return 2
        self.original = termios.tcgetattr(sys.stdin)
        try:
            tty.setraw(sys.stdin.fileno())
            while True:
                self.render()
                key = sys.stdin.read(1)
                if key == "q" or key == "\x03":
                    break
                if key in ("\x1b",):
                    seq = sys.stdin.read(2)
                    key = {"[A":"up", "[B":"down", "[C":"right", "[D":"left"}.get(seq, "")
                if key in ("j", "down") and self.entries:
                    self.index = min(len(self.entries)-1, self.index+1)
                elif key in ("k", "up") and self.entries:
                    self.index = max(0, self.index-1)
                elif key in ("h", "left", "\x7f", "\x08"):
                    self.cwd = self.cwd.parent
                    self.query = ""
                    self.refresh()
                elif key in ("\r", "\n", "right") and self.selected:
                    if self.selected.is_dir() and not self.selected.is_symlink():
                        self.cwd = self.selected.resolve()
                        self.index = 0
                        self.refresh()
                    else:
                        self.preview = True
                else:
                    self.operate(key)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.original)
            print(RESET + "\x1b[?25h")
        return 0


def main():
    parser = argparse.ArgumentParser(description="TERMAX visual filesystem explorer")
    parser.add_argument("directory", nargs="?", default=".")
    parser.add_argument("--sixel", action="store_true",
                        help="enable SIXEL image previews (requires a SIXEL-capable terminal)")
    args = parser.parse_args()
    try:
        explorer = Explorer(Path(args.directory))
        explorer.sixel = args.sixel or os.environ.get("TERMAX_SIXEL") == "1"
        return explorer.run()
    except Exception as exc:
        print(f"TERMAX Explorer error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
