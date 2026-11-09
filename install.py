#!/usr/bin/env python3
"""TERMAX 0.1.1 safety-gated installer.

The repository does not yet contain the complete 0.1.0 application source.
Preview is read-only. Apply is deliberately blocked until source recovery and
staged-upgrade tests are complete.
"""
from __future__ import annotations

import argparse
from pathlib import Path

VERSION = "0.1.1"
APP_REL = Path(".local/share/termax")
REQUIRED_SOURCE = (
    "termax/__init__.py",
    "termax/cli.py",
    "termax/registry.py",
    "termax/backup.py",
    "termax/system.py",
    "termax/commands/__init__.py",
    "termax/commands/core.py",
    "termax/commands/workspace.py",
    "termax/commands/config.py",
    "config/aliases.json",
    "config/functions.json",
    "config/plugins.json",
    "legacy/nexus.py",
)


def installed_version(app: Path) -> str:
    version_file = app / "VERSION"
    if version_file.is_file():
        try:
            return version_file.read_text(encoding="utf-8").strip() or "unknown"
        except OSError:
            return "unreadable"
    return "unknown"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="TERMAX Core installer (source-recovery safety gate)"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="requested installation; currently blocked until the complete source is recovered",
    )
    parser.add_argument(
        "--integrate-shell",
        action="store_true",
        help="request optional Zsh integration (also blocked until source recovery)",
    )
    args = parser.parse_args(argv)

    home = Path.home()
    app = home / APP_REL
    launcher = home / ".local/bin/tx"
    source_root = Path(__file__).resolve().parent / "src"
    missing = [rel for rel in REQUIRED_SOURCE if not (source_root / rel).is_file()]

    print(f"TERMAX installer {VERSION}")
    print(f"Application target: {app}")
    print(f"Launcher target:    {launcher}")
    if app.exists():
        print(f"Existing installation: {installed_version(app)}")
    else:
        print("Existing installation: not detected")
    print(f"Recovered source files: {len(REQUIRED_SOURCE) - len(missing)}/{len(REQUIRED_SOURCE)}")

    if not args.apply:
        print("Preview only. No files were created, replaced, or modified.")
        if missing:
            print("Source recovery is incomplete; installation is not available.")
            print("Missing source files:")
            for rel in missing:
                print(f"  - src/{rel}")
        print("The installed TERMAX application and launcher are not touched by preview.")
        return 0

    print("REFUSED: this repository does not contain a complete, verified TERMAX source payload.")
    print("No files were created, replaced, backed up, or modified.")
    if missing:
        print("Missing source files:")
        for rel in missing:
            print(f"  - src/{rel}")
    print("Recover the installed 0.1.0 source, add the verified payload, and implement")
    print("staged upgrade/rollback tests before enabling installation.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
