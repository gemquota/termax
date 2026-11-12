# TERMAX

TERMAX bootstraps and maintains both the native Termux environment and the user's Debian proot environment from one command centre.

## Install

    pkg update
    pkg install git python
    git clone https://github.com/gemquota/termax.git
    cd termax
    python install.py
    python install.py --apply
    export PATH="$HOME/.local/bin:$PATH"
    tx new --check
    tx new

The installer stages TERMAX and creates both `termax` and `tx` launchers. Run `tx new` for the complete native Termux **and Debian proot** environment bootstrap. It installs the Termux package manifest natively, then installs Debian equivalents inside the existing `debian` proot. Both environments receive Zsh, Oh My Zsh, Powerlevel10k, the managed Zsh plugins, and the declared Python dependencies. Use `tx new --minimal` for the essential toolchain or `tx new --check` for a read-only preview. Full setup is the default.

## Commands

Every command has a full name and a short alias. Both forms behave identically.

| Full command | Alias | Purpose |
|---|---|---|
| `tx new` | `tx n` | Initial environment bootstrap |
| `tx up` | `tx u` | Preflight, update, repair, audit and report |
| `tx ask` | `tx a` | Ask Gemini through the existing WW installation |
| `tx workspace` | `tx ws` | Inspect workspace tools |
| `tx files` | `tx fm` | Interactive file manager |
| `tx list` | `tx ls` | List files |
| `tx save` | `tx s` | Save a safe configuration archive |
| `tx load` | `tx l` | Validate and restore an archive |
| `tx config` | `tx c` | Show configuration |
| `tx plugins` | `tx p` | List integrations |

## Bootstrap and maintenance

- `tx new`: full setup by default; supports `--minimal`, `--full`, `--check`, and `--debug`.
- `tx up`: automatically runs preflight, updates native Termux packages, repairs the native Zsh stack, maintains Debian apt packages and its separate TERMAX Python venv, repairs the Debian Zsh stack, performs final audits in both environments, and writes `~/termax-report.txt`.
- `tx up --check`: read-only preflight for native Termux packages, Debian apt equivalents, Python modules, and Zsh components in both environments. It prints and reports the proposed maintenance plan without applying changes.
- `tx up --debug`: same maintenance workflow with detailed command output.
- Safe package updates and missing-manifest-package installs are automatic. TERMAX does not silently remove packages or overwrite personal configuration.
- Reports are never silently overwritten. If the default report exists, TERMAX offers a timestamped filename or another path.

Diagnostics are internal to `tx up`; there are no separate `doctor`, `status`, `dashboard`, `audit`, or `repair` commands.

## WW integration

WW remains installed in Debian proot. TERMAX installs its own separate Debian Python environment at `~/.local/share/termax/venv`; it does not reuse or replace WW's `.venv`, move the WW repository, or touch WW cookies. Debian-only packages that have no equivalent in the configured apt repositories are reported rather than silently substituted. Android-specific packages such as Termux:API remain native Termux packages.

    tx ask "Explain this Python traceback"

The bridge expects the Debian distribution to be named `debian` and WW at `/data/data/com.termux/files/home/ww`.

## Save and load

`tx save` creates a filtered archive of allowlisted configuration files. Credentials, SSH material, environment files and other sensitive paths are excluded. `tx load ARCHIVE` validates the archive and previews the files. Add `--apply` to restore; TERMAX asks for confirmation before replacing files and creates a rollback snapshot.

## File manager

    tx files ~/storage/shared
    tx list ~/storage/shared --thumbnails

Keys: arrows or j/k move; Enter opens; Backspace or b goes back; f forward; u up; c copy; x mark for move; p paste; v preview; q quit. Chafa Sixel previews require terminal-emulator support.

## Tests

    python -m unittest discover -s tests -v
