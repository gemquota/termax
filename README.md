# TERMAX Core

A Termux-first terminal workstation bootstrap. Python 3.11+, Zsh, optional Zellij/Rich.

## Version roadmap

- **0.1.0**: original TERMAX core baseline.
- **0.1.1**: current repository rebuild and maintenance release.
- **0.1.2**: next planned development release, carrying the workspace and shell expansion previously labelled 0.2.0.

## Fresh install

```bash
git clone https://github.com/gemquota/termax.git
cd termax
python install.py                 # preview only
python install.py --apply         # install core
export PATH="$HOME/.local/bin:$PATH"
tx doctor
tx status
tx dashboard
tx workspace layouts
```

To append the optional Zsh aliases/functions source block, use `python install.py --apply --integrate-shell` instead of the plain `--apply` command. Do not run both install commands back-to-back.

## Update an existing clone

```bash
cd ~/termax
git fetch origin
git checkout -B main origin/main
python install.py                 # preview
python install.py --apply         # install after reviewing preview
export PATH="$HOME/.local/bin:$PATH"
tx doctor
tx status
tx dashboard
```

Add `--integrate-shell` to the apply command only if you want TERMAX's optional Zsh integration. The installer backs up existing TERMAX app/launcher destinations before replacing them. It does not install packages. It does not edit shell startup files unless integration is explicitly requested.

## Workspace

`tx workspace layouts` lists bundled Zellij layouts. `tx workspace start default` or `tx workspace start dev` launches Zellij with the selected layout.

## Safety and scope

- Default installer mode is a preview.
- No package manager commands or network calls are run by the installer.
- Shell integration is opt-in and appends a marked block to `~/.zshrc`, preserving existing content.
- Existing app and launcher destinations are timestamp-backed up before replacement.
- This repository contains the `0.1.1` source rebuild. It is **not** a byte-for-byte reproduction of the earlier locally generated v0.1.0 archive, and this repository build has not yet been device-tested. Keep your existing working installation until you have reviewed and tested this rebuild.
