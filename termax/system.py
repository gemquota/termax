import importlib.util, os, platform, shutil
COMMANDS = ("zsh","git","python","fzf","zoxide","rg","fd","bat","eza","chafa","dot","nvim","vim","htop","btop","lazygit","zellij","tmux","gum","termux-battery-status","termux-clipboard-get","termux-notification")
MODULES = ("rich","cloudscraper","fastapi","httplib2","opentelemetry","requests","requests_toolbelt","uvicorn","textual","prompt_toolkit","plotext","networkx","yaml","typer")
def probe():
    found={n:shutil.which(n) for n in COMMANDS}
    mods={n:importlib.util.find_spec(n) is not None for n in MODULES}
    term=os.environ.get("TERM",""); color=os.environ.get("COLORTERM","")
    return {"platform":platform.platform(),"machine":platform.machine(),"python":platform.python_version(),"shell":os.environ.get("SHELL",""),"term":term,"colorterm":color,"is_termux":os.environ.get("PREFIX","").endswith("/com.termux/files/usr"),"commands":found,"modules":mods,"capabilities":{"zellij":bool(found["zellij"]),"tmux":bool(found["tmux"]),"rich":mods["rich"],"textual":mods["textual"],"termux_api":bool(found["termux-api"]),"truecolor_hint":color.lower() in ("truecolor","24bit"),"sixel":"unknown","kitty_graphics":"unknown","iterm2_images":"unknown"}}
