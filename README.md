# TERMAX 0.2.9

Termux-first terminal command centre. TERMAX targets Android/Termux and treats Sixel as a native graphics backend, with Termux:Monet as the preferred terminal emulator.

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

The first installer run is a read-only preview. The second explicitly applies the install. It stages the application under `~/.local/share/termax`, keeps a timestamped backup of an existing installation, and creates `termax` and `tx` launchers under `~/.local/bin`. It does not edit shell startup files.

## Preferred terminal: Termux:Monet

TERMAX is designed around the Sixel-capable Termux:Monet terminal experience. The newest accessible unarchived Monet fork found during this integration is https://github.com/JingMatrix/termux-monet (latest code push inspected: 28 August 2024). Its README documents Sixel and iTerm2 image protocols, and its terminal emulator source contains Sixel parsing, bitmap storage and Android canvas rendering.

The original Termux-Monet project is archived. Fork activity is limited, so treat unofficial APKs as experimental and verify their signatures and provenance. TERMAX does not silently install or replace your terminal emulator.

## Sixel setup and verification

Install an encoder inside Termux:

```sh
pkg install chafa
# or: pkg install libsixel
```

Then run:

```sh
termax graphics doctor
termax graphics demo
```

The demo emits a small Sixel test pattern. If it visibly renders in your terminal, enable Sixel output for TERMAX:

```sh
export TERMAX_SIXEL=1
```

To disable it:

```sh
export TERMAX_SIXEL=0
```

TERMAX deliberately does not infer Sixel support from `TERM=xterm-256color`, truecolour, the presence of Chafa, or the presence of libsixel. Those prove neither that the terminal parser is enabled nor that it can display the output.

## File browser

```sh
termax browse ~/storage/shared
termax ls ~/storage/shared --thumbnails
```

Keys: arrows or j/k move; Enter opens; Backspace or b goes back; f forward; u up; c copy; x mark for move; p paste; v preview; q quit. Mouse click selects and double-click enters directories where the terminal emulator forwards mouse events. Existing destinations are never overwritten. Symlink transfers are refused, and directory self-transfers are blocked.

Sixel previews require a verified Sixel-capable terminal and an installed encoder. The regular file list remains available without either.

## Other commands

`doctor`, `status`, `dashboard`, `workspace`, `plugin list`, `config show`, `backup`, and `restore ARCHIVE`. Restore is preview-only unless `--apply` is supplied. It validates archive paths against a strict allowlist, checks SHA-256 hashes and rejects symlinked parent directories.

## Tests

```sh
python -m unittest discover -s tests -v
```

The test suite covers CLI parsing, backup allowlisting, symlink-parent rejection, safe copy/move, collisions and directory self-transfer. Sixel display still needs visual verification in the actual Android terminal emulator.
