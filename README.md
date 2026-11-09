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

It creates termax-core-0.1.0-source.tar.gz in shared storage when available, otherwise in the home directory. The export contains the TERMAX application directory, excludes Python caches and backup archives, skips symlinks and common credential filenames, and prints a SHA-256 digest.

Review the archive before sharing it. Do not publish .dotfiles.md, GitHub authentication files, shell history, private keys, tokens or unrelated home-directory contents. The broad dotfiles acquisition archive is not a substitute for the TERMAX application source.

Attach the generated source archive so the missing modules can be recovered exactly. The next rebuild step is to compare and test the complete source tree, then implement a staged installer that preserves user configuration and can roll back safely.

## Device compatibility notes

The current scout inventory records Android 16 ARM64, Termux 0.118.3, Python 3.14.10, Zsh 5.9.2, Git 2.56.0 and Zellij. Zellij is the preferred multiplexer. Powerlevel10k is the active prompt; Starship is an alternative and should not be loaded alongside it.

Optional components must remain optional. In particular, do not install tmux, Textual, Termux:API or Termux:GUI merely because they appear in a roadmap. Verify compatibility and companion-app provenance first.
