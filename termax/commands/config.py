import json
from pathlib import Path
def base(): return Path(__file__).resolve().parents[2]/"config"
def plugin(args):
    d=json.loads((base()/"plugins.json").read_text())
    for p in d["plugins"]: print(f'{p["name"]:16} {p["status"]:22} {p["purpose"]}')
    return 0
def config(args):
    for name in ("aliases.json","functions.json"):
        print("\\n"+name.upper())
        for k,v in json.loads((base()/name).read_text()).items(): print(f"  {k:12} {v}")
    print("\\nRegistry is descriptive; shell config is not auto-injected.")
    return 0
