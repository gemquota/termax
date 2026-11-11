# TERMAX 0.2.9

Termux-first terminal command centre. This release restores the modular core supplied in the TERMAX Core v0.1 source archive and adds a full-screen terminal file navigator, safe session clipboard operations and optional Chafa Sixel previews.

## Install on Termux

```sh
pkg update
pkg install git python chafa -y
git clone https://github.com/gemquota/termax.git
cd termax
python install.py
python install.py --apply
export PATH="$HOME/.local/bin:$PATH"
termax --version
termax doctor
```

The first installer run is a read-only preview. The second explicitly applies the install. It stages the application under `~/.local/share/termax`, keeps a timestamped backup of an existing installation, and creates `termax` and `tx` launchers under `~/.local/bin`. It does not edit shell startup files.\n\n### Full Termux environment (Zsh, Oh My Zsh, tools and Python)\n\nThe environment bootstrap installs the explicit top-level Termux packages recorded by TERMAX Scout, the recorded and requested Python dependencies, Oh My Zsh, Powerlevel10k, and the archived Zsh plugin set. It preserves an existing `.zshrc` rather than replacing personal configuration. Review `config/termux-packages.txt` and `config/python-requirements.txt` before running.\n\n```sh\ngit pull --ff-only\nbash setup-termux.sh\nbash audit-termux.sh\n```\n\nThe bootstrap logs to `~/termax-bootstrap-*.log`. Package names unavailable in the configured Termux repositories are reported and cause a non-zero exit. `termux-api` also needs the separate Android Termux:API companion app and permissions. The audit checks command availability, Oh My Zsh, Powerlevel10k, plugins, and Python imports.

## Update

```sh
cd ~/termax
git pull --ff-only
python install.py
python install.py --apply
```

## File browser

```sh
termax browse ~/storage/shared
termax ls ~/storage/shared --thumbnails
```

Keys: arrows or j/k move; Enter opens; Backspace or b goes back; f forward; u up; c copy; x mark for move; p paste; v preview; q quit. Mouse click selects and double-click enters directories where the terminal emulator forwards mouse events. Existing destinations are never overwritten. Symlink transfers are refused, and directory self-transfers are blocked.

Chafa is optional. If installed, image previews are emitted as Sixel data. Sixel support is terminal-emulator-dependent and is not inferred from TERM or COLORTERM. If the emulator does not support Sixel, use the regular file list or disable thumbnails.

## Other commands

`doctor`, `status`, `dashboard`, `workspace`, `plugin list`, `config show`, `backup`, and `restore ARCHIVE`. Restore is preview-only unless `--apply` is supplied. It validates archive paths against a strict allowlist, checks SHA-256 hashes and rejects symlinked parent directories.

## Tests

```sh
python -m unittest discover -s tests -v
```

The test suite covers CLI parsing, backup allowlisting, symlink-parent rejection, safe copy/move, collisions and directory self-transfer. Sixel rendering and Android mouse forwarding require testing in the target terminal emulator.
