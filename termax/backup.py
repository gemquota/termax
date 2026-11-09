"""Filtered, integrity-checked TERMAX configuration backup and restore."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import stat
import tarfile
import tempfile
import time
from pathlib import Path, PurePosixPath

SAFE = (
    ".zshrc", ".p10k.zsh", ".gitconfig", ".config/starship.toml",
    ".config/zellij/config.kdl", ".termux/termux.properties",
    ".local/bin/combine-project", ".local/bin/weather",
)
DENY = {".ssh", ".gnupg", ".pki", "history", "hosts.yml", ".env",
        ".env.local", "id_rsa", "id_ed25519", "credentials.json"}
MAX_FILE = 2_000_000
MAX_TOTAL = 8_000_000
MAX_MANIFEST = 256_000
MAX_MEMBERS = 128


def safe_path(value: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("invalid archive path")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(x in ("", ".", "..") for x in path.parts):
        raise ValueError("unsafe archive path: " + value)
    if any(part in DENY for part in path.parts):
        raise ValueError("excluded archive path: " + value)
    return path


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def unique_path(directory: Path, prefix: str, suffix: str) -> Path:
    fd, name = tempfile.mkstemp(prefix=prefix, suffix=suffix, dir=directory)
    os.close(fd)
    return Path(name)


def backup(args: argparse.Namespace) -> int:
    out = Path.home() / ".local/share/termax/backups"
    out.mkdir(parents=True, exist_ok=True)
    target = unique_path(out, "termax-home-", ".tar.gz")
    entries = []
    try:
        with tarfile.open(target, "w:gz") as tf:
            for rel in SAFE:
                path = Path.home() / rel
                if not path.is_file() or path.is_symlink():
                    continue
                safe_path(rel)
                data = path.read_bytes()
                if len(data) > MAX_FILE:
                    continue
                info = tarfile.TarInfo("payload/" + rel)
                info.size = len(data)
                info.mode = stat.S_IMODE(path.stat().st_mode)
                tf.addfile(info, io.BytesIO(data))
                entries.append({"path": rel, "sha256": digest(data),
                                "size": len(data), "mode": info.mode})
            raw = json.dumps({"schema": 1, "files": entries},
                             separators=(",", ":")).encode()
            info = tarfile.TarInfo("manifest.json")
            info.size = len(raw)
            tf.addfile(info, io.BytesIO(raw))
        # Verify the completed archive before reporting it as usable.
        load(target)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    print("Backup:", target)
    print("Files:", len(entries))
    return 0


def load(path: Path) -> dict[str, tuple[bytes, int]]:
    total = 0
    with tarfile.open(path, "r:gz") as tf:
        members = tf.getmembers()
        if len(members) > MAX_MEMBERS:
            raise ValueError("too many archive members")
        names = [m.name for m in members]
        if len(names) != len(set(names)):
            raise ValueError("duplicate archive members")
        by_name = {m.name: m for m in members}
        manifest_member = by_name.get("manifest.json")
        if not manifest_member or not manifest_member.isfile() or manifest_member.size > MAX_MANIFEST:
            raise ValueError("manifest missing or too large")
        stream = tf.extractfile(manifest_member)
        if stream is None:
            raise ValueError("manifest unreadable")
        manifest = json.load(stream)
        if not isinstance(manifest, dict) or manifest.get("schema") != 1:
            raise ValueError("unsupported manifest schema")
        files = manifest.get("files")
        if not isinstance(files, list) or len(files) > MAX_MEMBERS - 1:
            raise ValueError("invalid manifest files")
        result = {}
        for item in files:
            if not isinstance(item, dict):
                raise ValueError("invalid manifest entry")
            rel = str(safe_path(item.get("path")))
            if rel in result:
                raise ValueError("duplicate manifest path")
            member = by_name.get("payload/" + rel)
            if not member or not member.isfile() or member.size > MAX_FILE:
                raise ValueError("missing or oversized payload")
            total += member.size
            if total > MAX_TOTAL:
                raise ValueError("archive payload exceeds total size limit")
            source = tf.extractfile(member)
            if source is None:
                raise ValueError("payload unreadable")
            data = source.read(MAX_FILE + 1)
            if (len(data) != item.get("size") or len(data) != member.size
                    or digest(data) != item.get("sha256")):
                raise ValueError("payload hash/size mismatch")
            mode = item.get("mode", 0o600)
            if not isinstance(mode, int) or mode < 0 or mode > 0o777:
                raise ValueError("invalid file mode")
            result[rel] = (data, mode)
        expected = {"manifest.json"} | {"payload/" + name for name in result}
        if set(names) != expected:
            raise ValueError("unlisted archive entries")
        return result


def checked_destination(home: Path, rel: str) -> Path:
    relative = safe_path(rel)
    current = home
    for part in relative.parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise ValueError("refusing symlinked parent directory: " + str(current))
        if current.exists() and not current.is_dir():
            raise ValueError("destination parent is not a directory: " + str(current))
    destination = home.joinpath(*relative.parts)
    if destination.is_symlink():
        raise ValueError("refusing symlink destination: " + str(destination))
    if destination.exists() and not destination.is_file():
        raise ValueError("refusing non-regular destination: " + str(destination))
    return destination


def restore(args: argparse.Namespace) -> int:
    try:
        payload = load(Path(args.archive).expanduser())
    except Exception as exc:
        print("ERROR:", exc)
        return 2
    home = Path.home()
    print("Validated", len(payload), "file(s)")
    for rel in payload:
        destination = checked_destination(home, rel)
        print(" ", "REPLACE" if destination.exists() else "CREATE", destination)
    if not args.apply:
        print("DRY RUN. No files changed. Add --apply to restore.")
        return 0

    old = {}
    for rel in payload:
        destination = checked_destination(home, rel)
        if destination.exists():
            old[rel] = (destination.read_bytes(), stat.S_IMODE(destination.stat().st_mode))

    rollback = unique_path(home, ".termax-rollback-", ".tar.gz")
    try:
        with tarfile.open(rollback, "w:gz") as tf:
            for rel, (data, mode) in old.items():
                info = tarfile.TarInfo("payload/" + rel)
                info.size = len(data)
                info.mode = mode
                tf.addfile(info, io.BytesIO(data))
    except Exception:
        rollback.unlink(missing_ok=True)
        raise

    completed = []
    temp_paths = []
    try:
        for rel, (data, mode) in payload.items():
            destination = checked_destination(home, rel)
            destination.parent.mkdir(parents=True, exist_ok=True)
            # Recheck after directory creation to catch pre-existing symlinks.
            destination = checked_destination(home, rel)
            fd, temporary = tempfile.mkstemp(prefix=".tx-restore-", dir=str(destination.parent))
            temp_paths.append(Path(temporary))
            with os.fdopen(fd, "wb") as output:
                output.write(data)
                output.flush()
                os.fsync(output.fileno())
            os.chmod(temporary, mode)
            os.replace(temporary, destination)
            temp_paths.pop()
            completed.append(rel)
    except Exception:
        for temporary in temp_paths:
            temporary.unlink(missing_ok=True)
        for rel in reversed(completed):
            destination = checked_destination(home, rel)
            if rel in old:
                data, mode = old[rel]
                fd, temporary = tempfile.mkstemp(prefix=".tx-rollback-", dir=str(destination.parent))
                with os.fdopen(fd, "wb") as output:
                    output.write(data)
                    output.flush()
                    os.fsync(output.fileno())
                os.chmod(temporary, mode)
                os.replace(temporary, destination)
            else:
                destination.unlink(missing_ok=True)
        print("Restore rolled back where possible. Snapshot:", rollback)
        raise

    print("Restored", len(completed), "files. Pre-restore snapshot:", rollback)
    return 0


def add_subcommands(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("backup", help="create filtered local config backup")
    parser.set_defaults(handler=backup)
    parser = sub.add_parser("restore", help="preview/apply validated backup")
    parser.add_argument("archive")
    parser.add_argument("--apply", action="store_true")
    parser.set_defaults(handler=restore)
