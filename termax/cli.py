#!/usr/bin/env python3
"""TERMAX command line interface with full names and compact aliases."""
import argparse
import importlib
from termax import __version__

COMMANDS = (
    ("new", "n", "Bootstrap the complete native Termux environment."),
    ("up", "u", "Preflight, maintain, repair, audit and report."),
    ("ask", "a", "Ask Gemini through the existing WW installation."),
    ("workspace", "ws", "Inspect terminal workspace tools."),
    ("files", "fm", "Open the interactive file manager."),
    ("list", "ls", "List files."),
    ("save", "s", "Create a safe TERMAX configuration archive."),
    ("load", "l", "Validate and restore a saved archive."),
    ("config", "c", "Show TERMAX configuration."),
    ("plugins", "p", "List TERMAX integrations."),
)

def _parser():
    p = argparse.ArgumentParser(prog="tx", description=f"TERMAX command center {__version__}")
    p.add_argument("--version", "-v", action="version", version=__version__)
    sub = p.add_subparsers(dest="command")
    for name, alias, summary in COMMANDS:
        q = sub.add_parser(name, aliases=[alias], help=f"{summary} (alias: {alias})")
        if name == "new":
            mode = q.add_mutually_exclusive_group()
            mode.add_argument("--minimal", action="store_true")
            mode.add_argument("--full", action="store_true")
            q.add_argument("--check", action="store_true")
            q.add_argument("--debug", action="store_true")
            q.set_defaults(module="termax.commands.lifecycle", function="new")
        elif name == "up":
            q.add_argument("--check", action="store_true")
            q.add_argument("--debug", action="store_true")
            q.set_defaults(module="termax.commands.lifecycle", function="up")
        elif name == "ask":
            q.add_argument("--new", dest="new_chat", action="store_true")
            q.add_argument("--debug", action="store_true")
            q.add_argument("prompt", nargs=argparse.REMAINDER)
            q.set_defaults(module="termax.commands.ww", function="ask")
        elif name == "workspace":
            q.set_defaults(module="termax.commands.workspace", function="workspace")
        elif name == "files":
            q.add_argument("path", nargs="?", default=".")
            q.set_defaults(handler="browse")
        elif name == "list":
            q.add_argument("path", nargs="?", default=".")
            q.add_argument("--thumbnails", action="store_true")
            q.set_defaults(handler="list")
        elif name == "save":
            q.set_defaults(module="termax.backup", function="backup")
        elif name == "load":
            q.add_argument("archive")
            q.add_argument("--apply", action="store_true")
            q.add_argument("--confirmed", action="store_true", help=argparse.SUPPRESS)
            q.set_defaults(module="termax.backup", function="restore")
        elif name == "config":
            q.set_defaults(module="termax.commands.config", function="config")
        elif name == "plugins":
            q.set_defaults(module="termax.commands.config", function="plugin")
    return p

def main(argv=None):
    p = _parser()
    args = p.parse_args(argv)
    if not args.command:
        p.print_help()
        return 0
    aliases = {alias: name for name, alias, _ in COMMANDS}
    args.command = aliases.get(args.command, args.command)
    if getattr(args, "handler", None):
        from termax.browser import browse, list_files
        if args.handler == "browse":
            browse(args.path)
        else:
            list_files(args.path, args.thumbnails)
        return 0
    module = importlib.import_module(args.module)
    return getattr(module, args.function)(args)

if __name__ == "__main__":
    raise SystemExit(main())
