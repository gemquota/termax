import subprocess, sys
from pathlib import Path
from termax.system import probe
def status(args):
    d=probe(); print("TERMAX CORE 0.2.9")
    for k in ("platform","machine","python","shell","term","colorterm","is_termux"): print(f"{k:14} {d[k]}")
    print("Zellij:", "available" if d["capabilities"]["zellij"] else "missing")
    print("Chafa:", d["commands"]["chafa"] or "not installed")
    print("Sixel: terminal support is not assumed; test preview on-device."); return 0
def doctor(args):
    d=probe(); checks=[("Python >= 3.11",sys.version_info >= (3,11)),("Git",bool(d["commands"]["git"])),("Zsh",bool(d["commands"]["zsh"]))]
    print("TERMAX DOCTOR")
    for n,ok in checks: print(f"[{'PASS' if ok else 'INFO'}] {n}")
    print("Read-only check. No packages installed and no files changed.")
    return 0 if checks[0][1] and checks[1][1] else 1
def dashboard(args):
    d=probe()
    try:
        from rich.console import Console
        from rich.table import Table
        c=Console(); t=Table(title="TERMAX / SYSTEM"); t.add_column("Capability"); t.add_column("State")
        for n in ("git","zellij","tmux","fzf","chafa","termux-api"): t.add_row(n,d["commands"][n] or "not installed")
        c.print(t)
    except ImportError: status(args)
    return 0
def nexus_legacy(args):
    script=Path(__file__).resolve().parents[2]/"legacy"/"nexus.py"
    if not script.is_file(): print("NEXUS legacy source missing."); return 2
    return subprocess.call([sys.executable,str(script),*args.extra])
