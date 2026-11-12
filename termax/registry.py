"""Canonical public command inventory. Diagnostics are internal to tx up."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Command:
    name: str
    alias: str
    summary: str

COMMANDS = (
    Command("new", "n", "Bootstrap the complete native Termux environment."),
    Command("up", "u", "Maintain, repair, audit and report."),
    Command("ask", "a", "Ask Gemini through the existing WW installation."),
    Command("workspace", "ws", "Inspect terminal workspace tools."),
    Command("files", "fm", "Open the interactive file manager."),
    Command("list", "ls", "List files."),
    Command("save", "s", "Create a safe TERMAX configuration archive."),
    Command("load", "l", "Validate and restore a saved archive."),
    Command("config", "c", "Show TERMAX configuration."),
    Command("plugins", "p", "List TERMAX integrations."),
)
