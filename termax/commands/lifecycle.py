"""Unified TERMAX bootstrap and maintenance workflows."""
from __future__ import annotations
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from shutil import which
from termax.system import probe

ROOT = Path(__file__).resolve().parents[2]
PACKAGE_MANIFEST = ROOT / "config" / "termux-packages.txt"
PYTHON_MANIFEST = ROOT / "config" / "python-requirements.txt"

def _manifest(path):
    if not path.is_file():
        return []
    return [line.split("#", 1)[0].strip() for line in path.read_text(encoding="utf-8").splitlines()
            if line.split("#", 1)[0].strip()]

def _run(command, debug=False, env=None):
    if debug:
        print("+", shlex.join([str(x) for x in command]))
        return subprocess.run(command, check=False, env=env).returncode
    result = subprocess.run(command, check=False, text=True, capture_output=True, env=env)
    if result.returncode:
        detail = (result.stderr or result.stdout or "").strip()
        print(f"[FAILED] {shlex.join([str(x) for x in command])}")
        if detail:
            print(detail[-2000:])
    return result.returncode

def _is_termux():
    return os.environ.get("PREFIX", "").endswith("/com.termux/files/usr") and which("pkg")

def _report_path():
    default = Path.home() / "termax-report.txt"
    if not default.exists():
        return default
    dated = Path.home() / f"termax-report-{time.strftime('%Y%m%d-%H%M%S')}.txt"
    print(f"Report already exists: {default}")
    if sys.stdin.isatty():
        answer = input(f"Use dated report {dated.name}? [Y/n] ").strip().lower()
        if answer in ("", "y", "yes"):
            return dated
        custom = input("Enter another report path (blank to cancel report only): ").strip()
        return Path(custom).expanduser() if custom else None
    print(f"Preserving existing report; writing {dated}")
    return dated

def _write_report(lines):
    target = _report_path()
    if target is None:
        print("Report generation cancelled; existing report preserved.")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        print(f"Refusing to overwrite existing report: {target}", file=sys.stderr)
        return
    target.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"Report: {target}")

def _package_state(package):
    result = subprocess.run(["dpkg-query", "-W", "-f=${Status}", package], capture_output=True, text=True)
    return result.returncode == 0 and "install ok installed" in result.stdout

def new(args):
    if not _is_termux():
        print("Run tx new from native Termux, not inside Debian proot.", file=sys.stderr)
        return 2
    packages = _manifest(PACKAGE_MANIFEST)
    requirements = _manifest(PYTHON_MANIFEST)
    if args.minimal:
        essentials = {"bash", "ca-certificates", "curl", "git", "python", "python-pip", "zsh", "zsh-completions", "fzf", "ripgrep", "fd", "jq"}
        packages = [p for p in packages if p in essentials]
    print("TERMAX minimal bootstrap" if args.minimal else "TERMAX full environment bootstrap")
    print(f"Planned Termux packages: {len(packages)}")
    print(f"Planned Python requirements: {len(requirements)}")
    print("WW in Debian proot is left untouched.")
    if args.check:
        missing = [p for p in packages if not _package_state(p)]
        print(f"Read-only preview: {len(missing)} Termux packages missing.")
        if missing:
            print("Would install:", ", ".join(missing))
        return 0
    script = ROOT / "setup-termux.sh"
    if not script.is_file():
        print("Bootstrap module is missing:", script, file=sys.stderr)
        return 2
    env = os.environ.copy()
    if args.minimal:
        env["TERMAX_MINIMAL"] = "1"
    if args.debug:
        env["TERMAX_DEBUG"] = "1"
    return _run(["bash", str(script)], debug=args.debug, env=env)

def up(args):
    if not _is_termux():
        print("TERMAX maintenance must run inside native Termux.", file=sys.stderr)
        return 2
    data = probe()
    packages = _manifest(PACKAGE_MANIFEST)
    missing = [p for p in packages if not _package_state(p)]
    lines = [
        "TERMAX MAINTENANCE REPORT",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S %Z')}",
        f"Platform: {data['platform']}",
        f"Architecture: {data['machine']}",
        f"Python: {data['python']}",
        f"Shell: {data['shell']}",
        "",
        "PREFLIGHT",
        f"Manifest packages: {len(packages)}",
        f"Missing packages: {len(missing)}",
        "Missing: " + (", ".join(missing) if missing else "none"),
    ]
    print("TERMAX preflight complete.")
    print(f"Packages missing: {len(missing)}")
    if args.check:
        print("READ-ONLY CHECK: no changes will be made.")
        lines += ["", "MODE: read-only check", "No changes applied."]
        _write_report(lines)
        return 0
    failures = []
    print("Updating package indexes...")
    if _run(["pkg", "update", "-y"], args.debug):
        failures.append("pkg update")
    print("Upgrading installed packages...")
    if _run(["pkg", "upgrade", "-y"], args.debug):
        failures.append("pkg upgrade")
    for package in missing:
        print(f"Installing missing package: {package}")
        if _run(["pkg", "install", "-y", package], args.debug):
            failures.append(f"pkg install {package}")
    print("Refreshing declared Python dependencies...")
    if _run([sys.executable, "-m", "pip", "install", "-r", str(PYTHON_MANIFEST)], args.debug):
        failures.append("Python requirements")
    final_missing = [p for p in packages if not _package_state(p)]
    lines += [
        "", "MODE: maintenance",
        "Actions: pkg update, pkg upgrade, install missing manifest packages, pip requirements",
        f"Final missing packages: {len(final_missing)}",
        "Final missing: " + (", ".join(final_missing) if final_missing else "none"),
        "Failures: " + (", ".join(failures) if failures else "none"),
        "", "DIAGNOSTICS",
    ]
    for name, path in data["commands"].items():
        lines.append(f"{name}: {path or 'missing'}")
    for name, present in data["modules"].items():
        lines.append(f"python module {name}: {'present' if present else 'missing'}")
    _write_report(lines)
    if failures or final_missing:
        print("Maintenance finished with issues. See the report.")
        return 1
    print("Maintenance and final audit complete.")
    return 0
