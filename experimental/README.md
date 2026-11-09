# TERMAX experimental sidecars

These prototypes are deliberately separate from the 0.1.1 maintenance payload.
They use only the Python standard library and do not install packages.

## Explorer
`python experimental/termax_explore.py [directory]`

Keyboard: arrows or j/k move; Enter opens directories; Backspace/h goes up;
. toggles hidden files; / filters; p previews; n creates a directory; r renames;
c copies; m moves; d moves the selected item into the user's Trash; q exits.
It never permanently deletes files. Symlink copy/move is refused.

## Pulse
`python experimental/termax_pulse.py -- python -m unittest discover -s tests -v`

Pulse passes command output through and adds a reactive terminal waveform for
each output line. It is intended for non-interactive, line-oriented commands;
it does not pretend to be a PTY wrapper for full-screen or interactive programs.

## Shell layer
Source `shell/termax.zsh` from ~/.zshrc after prompt setup and completion
initialization. It defines py/py3, pyr, pym, project navigation, Git shortcuts,
and optional integrations. No existing .zshrc is modified automatically.
