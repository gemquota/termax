"""Termux file browser. Uses stdlib curses and optional Chafa Sixel output."""
import curses, os, shutil, stat, subprocess
from pathlib import Path
IMAGE={".png",".jpg",".jpeg",".gif",".webp",".bmp",".tif",".tiff",".avif"}
def entries(path):
    rows=[]
    for p in path.iterdir():
        try: rows.append((p,p.lstat()))
        except OSError: pass
    return sorted(rows,key=lambda x:(not stat.S_ISDIR(x[1].st_mode),x[0].name.casefold()))
def transfer(sources,destination,move=False):
    destination=Path(destination).resolve()
    if not destination.is_dir(): raise ValueError("destination is not a directory")
    done=[]
    for raw in sources:
        src=Path(raw)
        if src.is_symlink(): raise ValueError("symlink transfers are refused")
        if not src.exists(): raise FileNotFoundError(src)
        target=destination/src.name
        if target.exists() or target.is_symlink(): raise FileExistsError(target)
        if src.is_dir():
            try: destination.relative_to(src.resolve()); raise ValueError("cannot transfer a directory into itself")
            except ValueError as e:
                if str(e).startswith("cannot transfer"): raise
            if move: shutil.move(str(src),str(target))
            else: shutil.copytree(src,target,symlinks=True)
        elif move: shutil.move(str(src),str(target))
        else: shutil.copy2(src,target,follow_symlinks=False)
        done.append(target)
    return done
def preview(path):
    chafa=shutil.which("chafa")
    if not chafa: return "Chafa is not installed (optional)."
    try:
        r=subprocess.run([chafa,"--format=sixels","--size","60x20",str(path)],capture_output=True,timeout=5)
        if r.returncode or not r.stdout: return "Chafa could not render this image."
        curses.endwin(); os.write(1,r.stdout); input("\\nPreview: press Enter "); return "Preview closed."
    except (OSError,subprocess.TimeoutExpired): return "Preview failed or timed out."
def browse(start="."):
    root=Path(start).expanduser().resolve()
    if not root.is_dir(): raise NotADirectoryError(root)
    def screen(win):
        curses.curs_set(0)
        try: curses.mousemask(curses.ALL_MOUSE_EVENTS|curses.REPORT_MOUSE_POSITION)
        except curses.error: pass
        here=root; back=[]; forward=[]; idx=0; clip=[]; cut=False; msg="Enter open | Backspace back | u up | c copy | x cut | p paste | v preview | q quit"
        while True:
            win.erase(); h,w=win.getmaxyx()
            win.addnstr(0,0," TERMAX 0.3.0  "+str(here),max(1,w-1),curses.A_REVERSE)
            try: rows=entries(here)
            except OSError as e: rows=[]; msg=str(e)
            idx=max(0,min(idx,len(rows)-1))
            for i,(p,st) in enumerate(rows[:max(1,h-3)]):
                label=("> " if i==idx else "  ")+("DIR " if stat.S_ISDIR(st.st_mode) else "    ")+p.name
                if p in clip: label=("CUT " if cut else "COPY ")+label
                try: win.addnstr(i+1,0,label,max(1,w-1),curses.A_REVERSE if i==idx else 0)
                except curses.error: pass
            win.addnstr(h-2,0,msg,max(1,w-1)); win.addnstr(h-1,0,"Mouse click select / double-click open. Sixel requires emulator support.",max(1,w-1)); win.refresh()
            k=win.getch()
            if k in (ord("q"),27): break
            if k in (curses.KEY_UP,ord("k")): idx=max(0,idx-1)
            elif k in (curses.KEY_DOWN,ord("j")): idx=min(max(0,len(rows)-1),idx+1)
            elif k in (curses.KEY_BACKSPACE,127,8,ord("b")) and back: forward.append(here); here=back.pop(); idx=0
            elif k==ord("f") and forward: back.append(here); here=forward.pop(); idx=0
            elif k==ord("u") and here.parent!=here: back.append(here); here=here.parent; idx=0
            elif k in (10,13,curses.KEY_ENTER) and rows:
                p,st=rows[idx]
                if stat.S_ISDIR(st.st_mode): back.append(here); here=p; forward.clear(); idx=0
                elif p.suffix.lower() in IMAGE: msg=preview(p)
                else: msg="Selected "+p.name
            elif k==ord("v") and rows and rows[idx][0].suffix.lower() in IMAGE: msg=preview(rows[idx][0])
            elif k==ord("c") and rows: clip=[rows[idx][0]]; cut=False; msg="Copied to session clipboard"
            elif k==ord("x") and rows: clip=[rows[idx][0]]; cut=True; msg="Marked for move"
            elif k==ord("p") and clip:
                try: transfer(clip,here,cut); clip=[]; msg="Paste complete"
                except Exception as e: msg="Paste refused: "+str(e)
            elif k==curses.KEY_MOUSE:
                try:
                    _,mx,my,_,state=curses.getmouse(); n=my-1
                    if 0<=n<len(rows):
                        idx=n
                        if state & getattr(curses,"BUTTON1_DOUBLE_CLICKED",0) and stat.S_ISDIR(rows[idx][1].st_mode):
                            back.append(here); here=rows[idx][0]; forward.clear(); idx=0
                except curses.error: pass
    curses.wrapper(screen)
def list_files(path=".",thumbnails=False):
    for p,st in entries(Path(path).expanduser()):
        print(("/" if stat.S_ISDIR(st.st_mode) else " ")+f" {st.st_size:>10}  {p.name}")
        if thumbnails and p.suffix.lower() in IMAGE:
            chafa=shutil.which("chafa")
            if chafa:
                try:
                    r=subprocess.run([chafa,"--format=sixels","--size","16x8",str(p)],capture_output=True,timeout=4)
                    if r.returncode==0 and r.stdout: os.write(1,r.stdout+b"\\n")
                except (OSError,subprocess.TimeoutExpired): pass
