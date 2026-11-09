#!/usr/bin/env python3
"""TERMAX Core installer. Preview by default; --apply performs local writes."""
from __future__ import annotations
import argparse, os, platform, shutil, subprocess, sys, time
from pathlib import Path

VERSION = "0.1.01"
APP_REL = Path(".local/share/termax")
CLI = r'''from __future__ import annotations
import argparse, os, platform, shutil, sys
from pathlib import Path
VERSION = "0.1.01"
def has(n): return shutil.which(n) is not None
def doctor(_):
 print("TERMAX DOCTOR")
 for label,ok in [("Python >= 3.11",sys.version_info >= (3,11)),("Git",has("git")),("Zsh",has("zsh")),("Zellij",has("zellij")),("Rich",__import__("importlib").util.find_spec("rich") is not None)]:
  print(f"[{'PASS' if ok else 'INFO'}] {label}")
 print("[INFO] Textual (optional)")
 print("[INFO] Termux API (optional)")
 print("Read-only check. No packages installed and no files changed.")
def status(_):
 print(f"TERMAX CORE {VERSION}")
 print(f"platform       {platform.platform()}")
 print(f"machine        {platform.machine()}")
 print(f"python         {platform.python_version()}")
 print(f"shell          {os.environ.get('SHELL','unknown')}")
 print(f"term           {os.environ.get('TERM','unknown')}")
 print(f"colorterm      {os.environ.get('COLORTERM','unknown')}")
 print(f"is_termux      {Path('/data/data/com.termux').exists()}")
 for n in ("Zellij","Rich","Textual"):
  key=n.lower(); ok=has(key) if key=="zellij" else __import__("importlib").util.find_spec(key) is not None
  print(f"{n:14} {'available' if ok else 'optional / absent'}")
 print("Sixel / Kitty / iTerm2: unknown; terminal type does not prove support.")
def dashboard(_):
 rows=[("git",shutil.which("git") or "not installed"),("zellij",shutil.which("zellij") or "not installed"),("tmux",shutil.which("tmux") or "not installed"),("fzf",shutil.which("fzf") or "not installed"),("chafa",shutil.which("chafa") or "not installed"),("termux-api","not installed"),("Textual","optional")]
 try:
  from rich.console import Console
  from rich.table import Table
  t=Table(title="TERMAX / SYSTEM"); t.add_column("Capability"); t.add_column("State")
  for a,b in rows:t.add_row(a,b)
  Console().print(t)
 except Exception:
  print("TERMAX / SYSTEM")
  for a,b in rows:print(f"{a:14} {b}")
def workspace(a):
 root=Path(__file__).resolve().parent.parent/"config/zellij/layouts"
 if a.action=="layouts":
  for p in sorted(root.glob("*.kdl")):print(p.stem)
 elif a.action=="start":
  if not has("zellij"):raise SystemExit("Zellij is not installed.")
  layout=root/(a.layout+".kdl")
  if not layout.is_file():raise SystemExit("Unknown layout")
  os.execvp("zellij",["zellij","--layout",str(layout)])
def main():
 p=argparse.ArgumentParser(prog="tx"); s=p.add_subparsers(dest="cmd",required=True)
 for n,f in (("doctor",doctor),("status",status),("dashboard",dashboard)):
  q=s.add_parser(n);q.set_defaults(fn=f)
 w=s.add_parser("workspace");ws=w.add_subparsers(dest="action",required=True)
 q=ws.add_parser("layouts");q.set_defaults(fn=workspace)
 q=ws.add_parser("start");q.add_argument("layout",choices=("default","dev"));q.set_defaults(fn=workspace)
 a=p.parse_args();a.fn(a)
if __name__=="__main__":main()
'''
SHELL = """# TERMAX shell integration (namespaced)
alias txll='ls -lah'
alias txgs='git status --short --branch'
alias txgl='git log --oneline --decorate -12'
txmkcd() { mkdir -p -- "$1" && cd -- "$1"; }
"""
DEFAULT_LAYOUT = '''layout {
 pane split_direction="vertical" {
  pane size="65%" command="zsh"
  pane split_direction="horizontal" {
   pane command="zsh"
   pane command="zsh"
  }
 }
}
'''
DEV_LAYOUT = '''layout {
 pane split_direction="vertical" {
  pane size="60%" command="zsh"
  pane split_direction="horizontal" {
   pane command="zsh"
   pane command="zsh"
  }
 }
}
'''
def backup(p):
 if not p.exists(): return None
 stamp=time.strftime("%Y%m%d-%H%M%S")+f"-{time.time_ns()%1000000000:09d}"
 d=p.with_name(p.name+".backup-"+stamp)
 shutil.copytree(p,d) if p.is_dir() else shutil.copy2(p,d)
 return d
def main():
 ap=argparse.ArgumentParser(description="Install TERMAX Core")
 ap.add_argument("--apply",action="store_true")
 ap.add_argument("--integrate-shell",action="store_true")
 a=ap.parse_args();home=Path.home();app=home/APP_REL;launcher=home/".local/bin/tx"
 print("TERMAX installer "+VERSION);print("Application:",app);print("Launcher:   ",launcher)
 if not a.apply:
  print("Preview only. Re-run with --apply to install.");return 0
 for p in (app,launcher):
  b=backup(p)
  if b:print("Backed up:",b)
 (app/"termax").mkdir(parents=True,exist_ok=True)
 (app/"config/zellij/layouts").mkdir(parents=True,exist_ok=True)
 (app/"termax/__init__.py").write_text('__version__ = "0.1.01"\n',encoding="utf-8")
 (app/"termax/cli.py").write_text(CLI,encoding="utf-8")
 (app/"shell").mkdir(exist_ok=True)
 (app/"shell/termax.zsh").write_text(SHELL,encoding="utf-8")
 (app/"config/zellij/layouts/default.kdl").write_text(DEFAULT_LAYOUT,encoding="utf-8")
 (app/"config/zellij/layouts/dev.kdl").write_text(DEV_LAYOUT,encoding="utf-8")
 launcher.parent.mkdir(parents=True,exist_ok=True)
 launcher.write_text("#!/data/data/com.termux/files/usr/bin/sh\nPYTHON=python\nexport PYTHONPATH="+repr(str(app))+"\nexec \"$PYTHON\" -m termax.cli \"$@\"\n",encoding="utf-8")
 launcher.chmod(0o755)
 if a.integrate_shell:
  z=home/".zshrc";old=z.read_text(encoding="utf-8") if z.exists() else ""
  marker="# >>> TERMAX shell integration >>>"
  if marker not in old:
   b=backup(z)
   if b:print("Backed up:",b)
   block='\n'+marker+'\n[[ -r "$HOME/.local/share/termax/shell/termax.zsh" ]] && source "$HOME/.local/share/termax/shell/termax.zsh"\n# <<< TERMAX shell integration <<<\n'
   z.write_text(old.rstrip()+"\n"+block,encoding="utf-8")
 print("Installed. Ensure ~/.local/bin is on PATH, then run: tx doctor")
 if not a.integrate_shell:print("No shell startup files were modified.")
 return 0
if __name__=="__main__":raise SystemExit(main())
