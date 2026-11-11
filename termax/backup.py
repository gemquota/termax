import hashlib, io, json, os, tarfile, tempfile, time
from pathlib import Path, PurePosixPath
SAFE=(".zshrc",".p10k.zsh",".gitconfig",".config/starship.toml",".config/zellij/config.kdl",".termux/termux.properties",".local/bin/combine-project",".local/bin/weather")
DENY={".ssh",".gnupg",".pki","history","hosts.yml",".env",".env.local","id_rsa","id_ed25519","credentials.json"}
def safe_path(value):
    p=PurePosixPath(value)
    if p.is_absolute() or not p.parts or ".." in p.parts or any(x in DENY for x in p.parts) or str(p) not in SAFE: raise ValueError("path is not in the TERMAX backup allowlist: "+value)
    return p
def digest(data): return hashlib.sha256(data).hexdigest()
def backup(args):
    out=Path.home()/".local/share/termax/backups"; out.mkdir(parents=True,exist_ok=True)
    target=out/("termax-home-"+time.strftime("%Y%m%d-%H%M%S")+".tar.gz"); entries=[]
    with tarfile.open(target,"w:gz") as tf:
        for rel in SAFE:
            p=Path.home()/rel
            if not p.is_file() or p.is_symlink(): continue
            data=p.read_bytes(); info=tarfile.TarInfo("payload/"+rel); info.size=len(data); info.mode=p.stat().st_mode&0o777
            tf.addfile(info,io.BytesIO(data)); entries.append({"path":rel,"sha256":digest(data),"size":len(data),"mode":info.mode})
        raw=json.dumps({"schema":1,"files":entries},indent=2).encode(); info=tarfile.TarInfo("manifest.json"); info.size=len(raw); tf.addfile(info,io.BytesIO(raw))
    print("Backup:",target,"Files:",len(entries)); return 0
def load(path):
    with tarfile.open(path,"r:gz") as tf:
        members=tf.getmembers(); names=[m.name for m in members]
        if len(names)!=len(set(names)): raise ValueError("duplicate archive members")
        by={m.name:m for m in members}
        if "manifest.json" not in by or not by["manifest.json"].isfile(): raise ValueError("manifest missing")
        manifest=json.load(tf.extractfile(by["manifest.json"]))
        if manifest.get("schema")!=1: raise ValueError("unsupported schema")
        result={}
        for item in manifest.get("files",[]):
            rel=str(safe_path(item["path"])); m=by.get("payload/"+rel)
            if not m or not m.isfile() or m.size>2_000_000: raise ValueError("missing/unsafe payload")
            data=tf.extractfile(m).read()
            if len(data)!=item["size"] or digest(data)!=item["sha256"]: raise ValueError("hash/size mismatch")
            result[rel]=(data,int(item.get("mode",0o600))&0o777)
        if set(names)!={"manifest.json"}|{"payload/"+x for x in result}: raise ValueError("unlisted archive entries")
        return result
def safe_destination(home,rel):
    p=home/rel; cur=home
    for part in PurePosixPath(rel).parts[:-1]:
        cur=cur/part
        if cur.is_symlink(): raise ValueError("symlinked parent directory refused: "+str(cur))
    try: p.resolve(strict=False).relative_to(home.resolve())
    except ValueError: raise ValueError("destination escapes home")
    return p
def restore(args):
    try: payload=load(Path(args.archive).expanduser())
    except Exception as e: print("ERROR:",e); return 2
    home=Path.home(); print("Validated",len(payload),"file(s)")
    for rel in payload: print("CREATE/REPLACE",home/rel)
    if not args.apply: print("DRY RUN. Add --apply to restore."); return 0
    stamp=time.strftime("%Y%m%d-%H%M%S"); old={}
    for rel in payload:
        p=safe_destination(home,rel)
        if p.exists():
            if p.is_symlink() or not p.is_file(): raise ValueError("unsafe destination")
            old[rel]=(p.read_bytes(),p.stat().st_mode&0o777)
    rollback=home/(".termax-rollback-"+stamp+".tar.gz")
    with tarfile.open(rollback,"w:gz") as tf:
        for rel,(data,mode) in old.items():
            info=tarfile.TarInfo("payload/"+rel); info.size=len(data); info.mode=mode; tf.addfile(info,io.BytesIO(data))
    done=[]
    try:
        for rel,(data,mode) in payload.items():
            p=safe_destination(home,rel); p.parent.mkdir(parents=True,exist_ok=True); p=safe_destination(home,rel)
            if p.exists() and (p.is_symlink() or not p.is_file()): raise ValueError("unsafe destination")
            fd,tmp=tempfile.mkstemp(prefix=".tx-restore-",dir=str(p.parent))
            with os.fdopen(fd,"wb") as f: f.write(data)
            os.chmod(tmp,mode); os.replace(tmp,p); done.append(rel)
    except Exception:
        for rel in done:
            p=safe_destination(home,rel)
            if rel in old: p.write_bytes(old[rel][0]); os.chmod(p,old[rel][1])
            else: p.unlink(missing_ok=True)
        print("Rollback snapshot:",rollback); raise
    print("Restored",len(done),"files. Snapshot:",rollback); return 0
def add_subcommands(sub):
    p=sub.add_parser("backup",help="create filtered config backup"); p.set_defaults(handler=backup)
    p=sub.add_parser("restore",help="preview/apply validated backup"); p.add_argument("archive"); p.add_argument("--apply",action="store_true"); p.set_defaults(handler=restore)
