# TERMAX Core

A Termux-first terminal workstation project. The known-working device baseline is TERMAX Core **0.1.0**. The repository's **0.1.1** maintenance rebuild is currently in source-recovery and installer-safety work.

## Version roadmap

- **0.1.0**: original TERMAX core baseline, installed and verified on the target Termux device.
- **0.1.1**: maintenance rebuild. Preserve the 0.1.0 command/configuration contracts, recover the complete source, and validate a staged upgrade before enabling installation.
- **0.1.2**: planned shell, workspace, visual and Android integration expansion.

## Current safety status

**Do not apply the installer yet.** The repository does not contain the complete installed 0.1.0 application source. The installer now refuses apply requests and preview mode is read-only.

The installed 0.1.0 command surface includes:

- doctor, status, dashboard
- workspace
- plugin, config
- nexus-legacy
- backup, restore

Its modular implementation includes termax/registry.py, termax/backup.py, termax/system.py, command modules, JSON registries and the preserved NEXUS dashboard. The 0.1.1 repository must retain these interfaces and files rather than replacing them with a reduced CLI.

## Inspect the repository safely

~~~bash
git clone https://github.com/gemquota/termax.git
cd termax
python install.py
python -m unittest discover -s tests -v
~~~

The installer preview performs no writes. Apply currently exits with status 2 and explains why it refused.

## Recover the installed 0.1.0 source

Run the export utility on the Termux device where 0.1.0 is installed:

~~~bash
python tools/export-installed-core.py
~~~

It creates termax-core-0.1.0-source.tar.gz in shared storage when available, otherwise in the home directory. The export contains the TERMAX application directory, excludes Python caches and backup archives, skips symlinks and common credential filenames, and prints a SHA-256 digest. It refuses to overwrite an existing archive; use a different output path or pass --force only when replacement is intentional.

Review the archive before sharing it. Do not publish .dotfiles.md, GitHub authentication files, shell history, private keys, tokens or unrelated home-directory contents. The broad dotfiles acquisition archive is not a substitute for the TERMAX application source.

Attach the generated source archive so the missing modules can be recovered exactly. The next rebuild step is to compare and test the complete source tree, then implement a staged installer that preserves user configuration and can roll back safely.

## Device compatibility notes

The current scout inventory records Android 16 ARM64, Termux 0.118.3, Python 3.14.10, Zsh 5.9.2, Git 2.56.0 and Zellij. Zellij is the preferred multiplexer. Powerlevel10k is the active prompt; Starship is an alternative and should not be loaded alongside it.

Optional components must remain optional. In particular, do not install tmux, Textual, Termux:API or Termux:GUI merely because they appear in a roadmap. Verify compatibility and companion-app provenance first.


## 0.1.2 expansion track: shell + visual sidecars

The expansion work is being developed separately from the 0.1.1 maintenance rebuild.

### Modular Zsh productivity layer

The optional `shell/termax.zsh` adds Python shortcuts (`py`, `py3`, `pyr`, `pym`, `pyv`, `activate`, `pyc`, `pyd`, `pyi`), Node/npm shortcuts, directory helpers, Git shortcuts, process/filesystem helpers and optional integrations for eza, zoxide, fzf, bat and lazygit.

Preview it before sourcing. To try it in a cloned checkout:

~~~zsh
source ~/termax/shell/termax.zsh
~~~

It does not edit or replace `~/.zshrc`. Add that source line manually only after reviewing the file. Powerlevel10k remains the active prompt; this layer does not load Starship.

### Experimental visual tools

- `python experimental/termax_explore.py [directory]`: keyboard-driven filesystem explorer with filtering, hidden files, text/image previews (bat/chafa when available), editor handoff, create, rename, copy, move and reversible trash. It uses the Python standard library and does not permanently delete selected files.
- `python experimental/termax_pulse.py -- python -m unittest discover -s tests -v`: streams a non-interactive command's output and adds a reactive activity waveform.
- Add `--aquarium` to Pulse for a small ASCII reef whose state responds to output: errors disturb it, warnings create currents, and successful output helps it recover.

The explorer and pulse tools are prototypes, not yet wired into the installed `tx` command dispatcher. The Zsh layer provides `txe` and `txp` wrappers when the checkout is at `~/termax` or the sidecars are installed under `~/.local/share/termax/experimental`.

### Existing project reuse

The expansion research identified useful local projects:
- `gemquota/nexus-aquarium`: fixed-step simulation, behavioural systems and live telemetry. Its architecture is a strong candidate for a richer terminal aquarium renderer.
- `gemquota/aiscii`: ASCII video conversion and streaming progress. Its full media pipeline depends on FFmpeg and heavier backend services, so it should remain an optional bridge rather than a Termux core dependency.
- `gemquota/hydra`: visual experiments and generated assets that may inform future terminal themes and visual modes.
- `gemquota/golf`: existing Python CLI and interactive-dashboard patterns.

No public or connected repository under the exact `DayneK` account was discoverable in the linked GitHub context. The dotfiles repo may use another owner or repository name.

### Try the experimental sidecars

~~~bash
python experimental/termax_explore.py ~
python experimental/termax_pulse.py --aquarium -- python -m unittest discover -s tests -v
python -m unittest discover -s tests -v
~~~

These experiments do not install dependencies or alter the live Termux setup. They must pass automated and device-side tests before being promoted into the `tx` command surface.
