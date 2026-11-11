#!/usr/bin/env python3
import argparse, importlib
from termax.registry import COMMANDS
from termax import __version__
def main(argv=None):
    p=argparse.ArgumentParser(prog="termax",description=f"TERMAX command center {__version__}")
    p.add_argument("--version",action="version",version=__version__)
    sub=p.add_subparsers(dest="command")
    for c in COMMANDS:
        q=sub.add_parser(c.name,help=c.summary)
        if c.name=="nexus-legacy": q.add_argument("extra",nargs=argparse.REMAINDER)
        if c.name=="ask": q.add_argument("prompt",nargs=argparse.REMAINDER,help="prompt to send to Gemini through WW")
        if c.name=="plugin": q.add_argument("action",choices=("list",),nargs="?",default="list")
        if c.name=="config": q.add_argument("action",choices=("show",),nargs="?",default="show")
        q.set_defaults(module=c.module,function=c.function)
    b=sub.add_parser("browse",help="interactive file browser"); b.add_argument("path",nargs="?",default=".")
    l=sub.add_parser("ls",help="list files"); l.add_argument("path",nargs="?",default="."); l.add_argument("--thumbnails",action="store_true")
    from termax.backup import add_subcommands
    add_subcommands(sub)
    a=p.parse_args(argv)
    if not a.command: p.print_help(); return 0
    if a.command=="browse":
        from termax.browser import browse
        browse(a.path); return 0
    if a.command=="ls":
        from termax.browser import list_files
        list_files(a.path,a.thumbnails); return 0
    if hasattr(a,"handler"): return a.handler(a)
    return getattr(importlib.import_module(a.module),a.function)(a)
if __name__=="__main__": raise SystemExit(main())
