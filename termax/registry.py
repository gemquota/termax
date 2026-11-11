from dataclasses import dataclass
@dataclass(frozen=True)
class Command:
    name: str
    summary: str
    module: str
    function: str
COMMANDS = (
    Command("doctor","Check platform and capabilities.","termax.commands.core","doctor"),
    Command("status","Show device and TERMAX status.","termax.commands.core","status"),
    Command("dashboard","Show terminal dashboard.","termax.commands.core","dashboard"),
    Command("workspace","Inspect Zellij and tmux.","termax.commands.workspace","workspace"),
    Command("ask","Ask Gemini through the existing WW installation in Debian proot.","termax.commands.ww","ask"),
    Command("plugin","List optional integrations.","termax.commands.config","plugin"),
    Command("config","Show alias and function registries.","termax.commands.config","config"),
    Command("nexus-legacy","Run preserved NEXUS dashboard.","termax.commands.core","nexus_legacy"),
)
