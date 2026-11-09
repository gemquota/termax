#!/usr/bin/env python3
"""Export the installed TERMAX application source for a controlled rebuild."""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import tempfile
import tarfile
from pathlib import Path

APP_REL = Path(".local/share/termax")
EXCLUDED_DIRS = {"__pycache__", "backups", "backup", ".git", "logs"}
EXCLUDED_NAMES = {
    ".env", ".env.local", ".netrc", "hosts.yml", "credentials.json",
    "id_rsa", "id_ed25519", "secrets.json", "token",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".log", ".sqlite", ".sqlite3", ".db"}
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_TOTAL_BYTES = 100 * 1024 * 1024


def is_excluded(path: Path) -> bool:
    if any(
        part in EXCLUDED_DIRS or part.startswith("backup-") or ".backup-" in part
        for part in path.parts
    ):
        return True
    if path.name in EXCLUDED_NAMES or path.name.startswith(".env."):
        return True
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True
    return False


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def export(source: Path, output: Path, *, force: bool = False) -> tuple[int, str]:
    required = (
        source / "VERSION",
        source / "termax/cli.py",
        source / "termax/registry.py",
        source / "termax/backup.py",
    )
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        raise ValueError("TERMAX source tree is incomplete: " + ", ".join(missing))
    if output.is_symlink():
        raise ValueError("refusing to replace a symlink output")
    if output.exists() and not force:
        raise FileExistsError(
            f"output already exists: {output}; choose another --output or pass --force"
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    candidates = []
    total = 0
    for path in sorted(source.rglob("*")):
        rel = path.relative_to(source)
        if is_excluded(rel) or path.is_symlink() or not path.is_file():
            continue
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            print(f"SKIP oversized file: {rel} ({size} bytes)")
            continue
        total += size
        if total > MAX_TOTAL_BYTES:
            raise ValueError("source export exceeds the 100 MiB safety limit")
        candidates.append((path, rel))

    fd, temp_name = tempfile.mkstemp(
        prefix=".termax-source-", suffix=".tar.gz", dir=str(output.parent)
    )
    os.close(fd)
    temp = Path(temp_name)
    try:
        with tarfile.open(temp, "w:gz") as archive:
            for path, rel in candidates:
                archive.add(path, arcname=rel.as_posix(), recursive=False)
        with tarfile.open(temp, "r:gz") as archive:
            members = archive.getmembers()
            if not members or any(not member.isfile() for member in members):
                raise ValueError("archive verification failed")
        os.chmod(temp, 0o600)
        if force:
            os.replace(temp, output)
        else:
            # O_EXCL makes creation fail atomically if the destination already
            # exists, including a symlink. This avoids relying on os.link(),
            # which is unavailable in some constrained Android Python builds.
            fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                with os.fdopen(fd, "wb") as destination, temp.open("rb") as source_file:
                    shutil.copyfileobj(source_file, destination)
                    destination.flush()
                    os.fsync(destination.fileno())
            except Exception:
                output.unlink(missing_ok=True)
                raise
            else:
                temp.unlink()
    except Exception:
        temp.unlink(missing_ok=True)
        raise

    return len(candidates), sha256(output)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path.home() / APP_REL)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace an existing archive at the selected output path",
    )
    args = parser.parse_args(argv)

    shared = Path.home() / "storage/shared"
    default_output = (
        shared / "termax-core-0.1.0-source.tar.gz"
        if shared.is_dir()
        else Path.home() / "termax-core-0.1.0-source.tar.gz"
    )
    output = (args.output or default_output).expanduser()
    source = args.source.expanduser()

    try:
        count, digest = export(source, output, force=args.force)
    except (OSError, ValueError, tarfile.TarError) as exc:
        parser.exit(2, f"ERROR: {exc}\n")

    print(f"Source: {source}")
    print(f"Archive: {output}")
    print(f"Files: {count}")
    print(f"SHA-256: {digest}")
    print("Review the archive before sharing; this exports the TERMAX app tree only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
