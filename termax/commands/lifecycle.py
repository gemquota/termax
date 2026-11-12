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
PLUGIN_REPOS = {
    "themes/powerlevel10k": "https://github.com/romkatv/powerlevel10k.git",
    "plugins/zsh-autosuggestions": "https://github.com/zsh-users/zsh-autosuggestions.git",
    "plugins/zsh-syntax-highlighting": "https://github.com/zsh-users/zsh-syntax-highlighting.git",
    "plugins/zsh-autocomplete": "https://github.com/marlonrichert/zsh-autocomplete.git",
    "plugins/zsh-history-substring-search": "https://github.com/zsh-users/zsh-history-substring-search.git",
}

def _manifest(path):
    if not path.is_file():
        return []
    return [line.split("#", 1)[0].strip() for line in path.read_text(encoding="utf-8").splitlines()
            if line.split("#", 1)[0].strip()]

def _run(command, debug=False, env=None, stream=False):
    if debug:
        print("+", shlex.join([str(x) for x in command]))
        stream = True
    if stream:
        return subprocess.run(command, check=False, env=env).returncode
    result = subprocess.run(command, check=False, text=True, capture_output=True, env=env)
    if result.returncode:
        detail = (result.stderr or result.stdout or "").strip()
        print(f"[FAILED] {shlex.join([str(x) for x in command])}")
        if detail:
            print(detail[-2000:])
    return result.returncode

def _proot_ready():
    if not which("proot-distro"):
        return False
    result = subprocess.run(
        ["proot-distro", "login", "debian", "--", "/bin/true"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0

def _proot_run(mode, debug=False, stream=True):
    script = ROOT / "termax" / "proot-bootstrap.sh"
    if not script.is_file():
        print("Debian proot bootstrap module is missing:", script, file=sys.stderr)
        return 2
    env = os.environ.copy()
    if debug:
        env["TERMAX_DEBUG"] = "1"
    command = [
        "proot-distro", "login", "debian", "--",
        "/bin/bash", "--noprofile", "--norc", str(script), mode,
    ]
    return _run(command, debug=debug, env=env, stream=stream)

def _ensure_debian(debug=False):
    if not which("proot-distro"):
        print("proot-distro is not installed. Install it with the native Termux package manifest.", file=sys.stderr)
        return False
    if _proot_ready():
        return True
    print("Debian proot is missing; installing the Debian distribution...")
    return _run(["proot-distro", "install", "debian"], debug=debug, stream=True) == 0 and _proot_ready()

def _is_termux():
    return os.environ.get("PREFIX", "").endswith("/com.termux/files/usr") and which("pkg")

def _report_path():
    default = Path.home() / "termax-report.txt"
    if not default.exists():
        return default
    dated = Path.home() / f"termax-report-{time.strftime('%Y%m%d-%H%M%S')}.txt"
    if dated.exists():
        dated = dated.with_name(dated.stem + f"-{os.getpid()}" + dated.suffix)
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
    try:
        with target.open("x", encoding="utf-8") as stream:
            stream.write("\n".join(lines).rstrip() + "\n")
    except FileExistsError:
        print(f"Refusing to overwrite existing report: {target}", file=sys.stderr)
        return
    print(f"Report: {target}")

def _package_state(package):
    result = subprocess.run(["dpkg-query", "-W", "-f=${Status}", package], capture_output=True, text=True)
    return result.returncode == 0 and "install ok installed" in result.stdout

def _zsh_audit():
    home = Path.home()
    custom = Path(os.environ.get("ZSH_CUSTOM", str(home / ".oh-my-zsh/custom")))
    checks = {
        "Oh My Zsh": (home / ".oh-my-zsh").is_dir(),
        ".zshrc": (home / ".zshrc").is_file(),
        "Powerlevel10k": (custom / "themes/powerlevel10k").is_dir(),
        "Powerlevel10k config": (home / ".p10k.zsh").is_file(),
    }
    for plugin in ("zsh-autosuggestions", "zsh-syntax-highlighting", "zsh-autocomplete", "zsh-history-substring-search"):
        checks[plugin] = (custom / "plugins" / plugin).is_dir()
    return checks

def _repair_zsh(debug, failures):
    home = Path.home()
    omz = home / ".oh-my-zsh"
    zshrc = home / ".zshrc"
    had_zshrc = zshrc.exists()
    if not omz.is_dir():
        installer = 'RUNZSH=no CHSH=no KEEP_ZSHRC=yes sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"'
        print("Installing missing Oh My Zsh...")
        if _run(["sh", "-c", installer], debug):
            failures.append("Oh My Zsh installation")
            return
    custom = Path(os.environ.get("ZSH_CUSTOM", str(omz / "custom")))
    for relative, url in PLUGIN_REPOS.items():
        destination = custom / relative
        if destination.is_dir() and (destination / ".git").is_dir():
            if _run(["git", "-C", str(destination), "pull", "--ff-only"], debug):
                failures.append("update " + relative)
        elif not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            if _run(["git", "clone", "--depth=1", url, str(destination)], debug):
                failures.append("install " + relative)
        else:
            print(f"[SKIP] Preserving non-git directory: {destination}")
    if not had_zshrc and not zshrc.exists():
        template = omz / "templates/zshrc.zsh-template"
        if template.is_file():
            zshrc.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
    if not had_zshrc and zshrc.exists():
        text = zshrc.read_text(encoding="utf-8")
        text = text.replace('ZSH_THEME="robbyrussell"', 'ZSH_THEME="powerlevel10k/powerlevel10k"')
        text = text.replace("plugins=(git)", "plugins=(git zsh-autosuggestions zsh-syntax-highlighting zsh-autocomplete zsh-history-substring-search colored-man-pages)")
        if "TERMAX_MANAGED_ZSH" not in text:
            text += "\n# TERMAX_MANAGED_ZSH\nexport PATH=\"$HOME/.local/bin:$PATH\"\n[[ -f \"$HOME/.p10k.zsh\" ]] && source \"$HOME/.p10k.zsh\"\n"
        zshrc.write_text(text, encoding="utf-8")
    elif had_zshrc:
        print("Existing .zshrc left untouched.")

def new(args):
    if not _is_termux():
        print("Run tx new from native Termux, not inside Debian proot.", file=sys.stderr)
        return 2
    packages = _manifest(PACKAGE_MANIFEST)
    requirements = _manifest(PYTHON_MANIFEST)
    if args.minimal:
        essentials = {"bash", "ca-certificates", "curl", "git", "python", "python-pip", "proot-distro", "zsh", "zsh-completions", "fzf", "ripgrep", "fd", "jq"}
        packages = [p for p in packages if p in essentials]
    print("TERMAX minimal bootstrap" if args.minimal else "TERMAX full environment bootstrap")
    print(f"Planned Termux packages: {len(packages)}")
    print(f"Planned Python requirements: {len(requirements)}")
    print("TERMAX manages both native Termux and Debian proot. WW itself remains untouched.")
    if args.check:
        missing = [p for p in packages if not _package_state(p)]
        print(f"Read-only preview: {len(missing)} native Termux packages missing.")
        if missing:
            print("Would install:", ", ".join(missing))
        if _proot_ready():
            print("Debian proot is present. Checking its package manifest...")
            _proot_run("check", debug=args.debug, stream=True)
        else:
            print("Debian proot is absent or not ready; tx new will install the Debian distribution and its TERMAX package set.")
        return 0
    script = ROOT / "termax" / "bootstrap.sh"
    if not script.is_file():
        print("Internal bootstrap module is missing:", script, file=sys.stderr)
        return 2
    env = os.environ.copy()
    if args.minimal:
        env["TERMAX_MINIMAL"] = "1"
    if args.debug:
        env["TERMAX_DEBUG"] = "1"
    return _run(["bash", str(script)], debug=args.debug, env=env, stream=True)

def up(args):
    if not _is_termux():
        print("TERMAX maintenance must run inside native Termux.", file=sys.stderr)
        return 2
    data = probe()
    packages = _manifest(PACKAGE_MANIFEST)
    missing = [p for p in packages if not _package_state(p)]
    zsh_preflight = _zsh_audit()
    missing_shell_preflight = [name for name, present in zsh_preflight.items() if not present]
    missing_modules = [name for name, present in data["modules"].items() if not present]
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
        f"Missing Python modules: {len(missing_modules)}",
        "Missing modules: " + (", ".join(missing_modules) if missing_modules else "none"),
        f"Missing Zsh components: {len(missing_shell_preflight)}",
        "Missing Zsh components: " + (", ".join(missing_shell_preflight) if missing_shell_preflight else "none"),
        "",
        "PROPOSED ACTION PLAN",
        "1. Refresh Termux package indexes.",
        "2. Upgrade installed Termux packages.",
        "3. Install missing packages from the TERMAX manifest.",
        "4. Refresh declared Python dependencies.",
        "5. Repair/update Oh My Zsh, Powerlevel10k and managed plugins.",
        "6. Install/maintain the Debian proot package set and isolated Python environment.",
        "7. Install/configure the Debian Oh My Zsh, Powerlevel10k and plugins.",
        "8. Run final audits in both environments.",
        f"Debian proot: {'present' if _proot_ready() else 'missing or not ready'}",
    ]
    print("TERMAX preflight complete.")
    print(f"Packages missing: {len(missing)} | Python modules missing: {len(missing_modules)} | Zsh components missing: {len(missing_shell_preflight)}")
    if args.check:
        print("READ-ONLY CHECK: proposed actions follow; no changes will be made.")
        for item in lines[lines.index("PROPOSED ACTION PLAN") + 1:]:
            print(item)
        if _proot_ready():
            print("Debian proot read-only package check:")
            _proot_run("check", debug=args.debug, stream=True)
        lines += ["", "MODE: read-only check", "No changes applied in either environment."]
        _write_report(lines)
        return 0
    failures = []
    print("Running the unified native Termux + Debian proot maintenance workflow...")
    bootstrap = ROOT / "termax" / "bootstrap.sh"
    env = os.environ.copy()
    if args.debug:
        env["TERMAX_DEBUG"] = "1"
    if _run(["bash", str(bootstrap)], debug=args.debug, env=env, stream=True):
        failures.append("dual-environment bootstrap/maintenance")
    final_missing = [p for p in packages if not _package_state(p)]
    final_data = probe()
    final_missing_modules = [name for name, present in final_data["modules"].items() if not present]
    zsh_checks = _zsh_audit()
    missing_shell = [name for name, present in zsh_checks.items() if not present]
    lines += [
        "", "MODE: maintenance",
        "Actions: native Termux package/Python/Zsh maintenance plus Debian apt packages, isolated Python venv, Oh My Zsh, Powerlevel10k and plugins",
        f"Final missing packages: {len(final_missing)}",
        "Final missing: " + (", ".join(final_missing) if final_missing else "none"),
        f"Final missing Python modules: {len(final_missing_modules)}",
        "Final missing modules: " + (", ".join(final_missing_modules) if final_missing_modules else "none"),
        f"Missing native Zsh components: {len(missing_shell)}",
        "Missing native Zsh components: " + (", ".join(missing_shell) if missing_shell else "none"),
        f"Debian proot: {'present' if _proot_ready() else 'not ready'}",
        "Failures: " + (", ".join(failures) if failures else "none"),
        "", "DIAGNOSTICS",
    ]
    for name, path in final_data["commands"].items():
        lines.append(f"{name}: {path or 'missing'}")
    for name, present in final_data["modules"].items():
        lines.append(f"python module {name}: {'present' if present else 'missing'}")
    for name, present in zsh_checks.items():
        lines.append(f"{name}: {'present' if present else 'missing'}")
    _write_report(lines)
    if failures or final_missing or final_missing_modules or missing_shell:
        print("Maintenance finished with issues. See the report.")
        return 1
    print("Maintenance and final audit complete.")
    return 0
