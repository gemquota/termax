import shutil, subprocess
def workspace(args):
    z=shutil.which("zellij"); tm=shutil.which("tmux")
    print("TERMAX WORKSPACE")
    if z:
        print("Zellij:",z)
        try:
            r=subprocess.run([z,"list-sessions"],capture_output=True,text=True,timeout=3)
            print((r.stdout or r.stderr).strip() or "No active sessions reported.")
        except Exception as e: print("Session query unavailable:",e)
    else: print("Zellij: not installed")
    print("tmux:",tm or "not installed (optional)")
    print("No session was created or modified."); return 0
