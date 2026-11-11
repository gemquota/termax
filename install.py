#!/usr/bin/env python3
"""TERMAX 0.2.9 staged installer. Preview is read-only."""
import argparse, os, shutil, sys, time
from pathlib import Path
SRC=Path(__file__).resolve().parent
HOME=Path.home(); APP=HOME/".local/share/termax"; BIN=HOME/".local/bin"
def main(argv=None):
    p=argparse.ArgumentParser(description="Install TERMAX 0.2.9 (preview by default)")
    p.add_argument("--apply",action="store_true"); a=p.parse_args(argv)
    print("TERMAX installer 0.2.9"); print("Application:",APP); print("Launchers:",BIN/"termax",BIN/"tx")
    if not a.apply: print("DRY RUN: no files changed. Re-run with --apply."); return 0
    required=("termax/__init__.py","termax/cli.py","termax/registry.py","termax/backup.py","termax/browser.py","termax/system.py","config/plugins.json","config/aliases.json","config/functions.json")
    missing=[x for x in required if not (SRC/x).is_file()]
    if missing:
        print("REFUSED: incomplete source tree:",", ".join(missing),file=sys.stderr); return 2
    stamp=time.strftime("%Y%m%d-%H%M%S"); APP.parent.mkdir(parents=True,exist_ok=True); BIN.mkdir(parents=True,exist_ok=True)
    staging=APP.with_name("termax.staging-"+stamp); backup=APP.with_name("termax.backup-"+stamp)
    try:
        staging.mkdir()
        for folder in ("termax","config","legacy"):
            if (SRC/folder).is_dir(): shutil.copytree(SRC/folder,staging/folder)
        (staging/"VERSION").write_text("0.2.9\n",encoding="utf-8")
        if APP.exists(): APP.rename(backup)
        try: staging.rename(APP)
        except Exception:
            if backup.exists() and not APP.exists(): backup.rename(APP)
            raise
        launcher='#!/usr/bin/env sh\nexport PYTHONPATH="'+str(APP)+'"\nexec python -m termax.cli "$@"\n'
        for name in ("termax","tx"):
            target=BIN/name; tmp=BIN/(name+".tmp")
            tmp.write_text(launcher,encoding="utf-8"); tmp.chmod(0o755); os.replace(tmp,target)
        print("Installed TERMAX 0.2.9.")
        if backup.exists(): print("Previous application backup:",backup)
        print("No shell startup files were modified. Ensure ~/.local/bin is on PATH.")
        return 0
    except Exception as e:
        if staging.exists(): shutil.rmtree(staging,ignore_errors=True)
        print("Installation failed:",e,file=sys.stderr); return 2
if __name__=="__main__": raise SystemExit(main())
