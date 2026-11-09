# TERMAX Core

Termux-first terminal workstation bootstrap. Python 3.11+, Zsh, optional Zellij/Rich.

## Install

```bash
git clone https://github.com/gemquota/termax.git
cd termax
python install.py                 # preview only
python install.py --apply         # install core
python install.py --apply --integrate-shell
export PATH="$HOME/.local/bin:$PATH"
tx doctor
tx status
tx dashboard
tx workspace layouts
```

The installer backs up existing TERMAX app/launcher destinations. It does not install packages. Shell integration is opt-in and appends a marked block to `~/.zshrc`, preserving existing content.

## Version

Repository bootstrap 0.1.1. This is a clean source rebuild, not a byte-for-byte reproduction of the earlier locally generated v0.1 archive.
