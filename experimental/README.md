# TERMAX experimental sidecars

These prototypes are deliberately separate from the 0.1.1 maintenance payload.
They use only the Python standard library and do not install packages.

## Explorer
`python experimental/termax_explore.py [directory]`

Keyboard: arrows or j/k move; Enter opens directories; Backspace/h goes up;
. toggles hidden files; / filters; p previews; v toggles SIXEL previews; o opens
the selected file in $EDITOR; n creates a directory; r renames; c copies; m moves;
d moves the selected item into the user's Trash; q exits. It never permanently
deletes files. Symlink copy/move is refused.

### SIXEL image mode

SIXEL is the preferred pixel-graphics experiment. It is opt-in because not every
terminal or multiplexer supports DEC SIXEL, and unsupported escape sequences can
make a mess of the display.

~~~bash
python experimental/termax_explore.py --sixel ~/Pictures
# or, after confirming terminal support:
export TERMAX_SIXEL=1
python experimental/termax_explore.py ~/Pictures
~~~

Inside Explorer, press `v` to toggle SIXEL previews. The renderer prefers
`chafa --format=sixels`, then falls back to `img2sixel`. Without an encoder,
it falls back to Chafa symbol art or a text preview. Install neither automatically.

Test SIXEL outside Zellij first. Multiplexers may not pass SIXEL control sequences
through, and Termux true-colour support does not prove SIXEL support. The user's
terminal emulator must explicitly support DEC SIXEL. Animated GIF previews are
rendered as a static frame when using img2sixel.

## Pulse
`python experimental/termax_pulse.py -- python -m unittest discover -s tests -v`

Pulse passes command output through and adds a reactive terminal waveform for
each output line. It is intended for non-interactive, line-oriented commands;
it does not pretend to be a PTY wrapper for full-screen or interactive programs.

## Shell layer
Source `shell/termax.zsh` from ~/.zshrc after prompt setup and completion
initialization. It defines py/py3, pyr, pym, project navigation, Git shortcuts,
and optional integrations. No existing .zshrc is modified automatically.

## Shell package shortcuts

- `pi package`: pip install package
- `pir`: pip install -r requirements.txt (or pass another requirements file)
- `pireq`: export the current environment to requirements.txt
- `pifreeze`, `pipls`, `pishow`, `pipu`: common pip operations
- `pki`, `pkui`, `pks`, `pkl`, `pkup`, `pkclean`: Termux pkg install,
  uninstall, search, list-installed, update/upgrade and clean
- `sixelon` / `sixeloff`: enable or disable opt-in SIXEL image previews
