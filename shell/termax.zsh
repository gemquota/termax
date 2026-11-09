# TERMAX shell layer: source from ~/.zshrc after compinit and prompt setup.
# Safe to source repeatedly. Optional tools are detected at call time.

# Python shortcuts
alias py='python'
alias py3='python3'
alias pipu='python -m pip install --upgrade'
alias pipls='python -m pip list'
pyr() { command python run.py "$@"; }
pym() { command python main.py "$@"; }
pyv() { command python -m venv "\${1:-.venv}"; }
activate() {
  local v="\${1:-.venv}"
  [[ -f "$v/bin/activate" ]] || { print -u2 "No venv activation script: $v/bin/activate"; return 1; }
  source "$v/bin/activate"
}

# Navigation and listing
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias .....='cd ../../../..'
alias c='clear'
alias cls='clear'
alias h='history'
alias j='jobs -l'
alias l='ls -lah'
alias ll='ls -lah'
alias la='ls -A'
alias lsd='ls -d */'
alias mkdir='mkdir -p'
mkcd() { [[ -n "$1" ]] || return 2; command mkdir -p -- "$1" && builtin cd -- "$1"; }
up() { local n="\${1:-1}"; while (( n-- > 0 )); do builtin cd .. || return; done; }
take() { [[ -n "$1" ]] || return 2; command mkdir -p -- "$1" && builtin cd -- "$1"; }
croot() { local root; root="$(git rev-parse --show-toplevel 2>/dev/null)" || return; builtin cd "$root"; }

# Python project helpers
pywhere() { command -v python; python --version; }
pyreq() { python -m pip freeze > "\${1:-requirements.txt}"; }
pyserve() { python -m http.server "\${1:-8000}"; }

# Git shortcuts, intentionally avoiding destructive force/reset aliases.
alias g='git'
alias gs='git status --short --branch'
alias gst='git status'
alias ga='git add'
alias gaa='git add -A'
alias gd='git diff'
alias gds='git diff --staged'
alias gl='git log --oneline --decorate -12'
alias gll='git log --graph --oneline --decorate --all'
alias gco='git checkout'
alias gsw='git switch'
alias gcm='git commit -m'
alias gpl='git pull --ff-only'
alias gps='git push'
alias gpf='git push --force-with-lease'
alias gcl='git clone'
alias gbr='git branch -vv'

# Search, preview and file tools
if (( $+commands[rg] )); then alias grep='rg'; fi
if (( $+commands[bat] )); then alias cat='bat --paging=never'; fi
if (( $+commands[eza] )); then
  alias ls='eza --icons --group-directories-first'
  alias ll='eza -lah --icons --group-directories-first'
  alias la='eza -lah --icons --group-directories-first --all'
fi
if (( $+commands[zoxide] )); then
  eval "$(zoxide init zsh)"
fi
if (( $+commands[fzf] )); then
  alias ff='fzf'
  alias ffd='find . -type d -not -path "*/.git/*" | fzf'
fi
if (( $+commands[lazygit] )); then alias lg='lazygit'; fi

# Python quality-of-life
alias pyd='python -m pdb'
alias pyi='python -i'
alias pyc='python -m compileall -q .'
alias pytest='python -m pytest'
alias pipup='python -m pip install --upgrade pip'
alias pipout='python -m pip freeze'

# Node/npm shortcuts (only meaningful in projects that use Node)
alias ni='npm install'
alias nid='npm install --save-dev'
alias nr='npm run'
alias nrd='npm run dev'
alias nrb='npm run build'
alias nrt='npm test'
alias npxc='npx'

# Filesystem and process helpers
alias dus='du -sh ./* 2>/dev/null | sort -h'
alias du1='du -h --max-depth=1 . 2>/dev/null | sort -h'
alias dfh='df -h'
alias psg='ps -ef | grep -i'
alias tree2='tree -L 2'
alias tree3='tree -L 3'
alias jfmt='python -m json.tool'
alias gss='git status --short'
alias glog='git log --graph --oneline --decorate -20'
alias gshow='git show --stat'

# TERMAX entry points
alias txs='tx status'
alias txd='tx doctor'
txe() {
  local root="${TERMAX_REPO:-$HOME/termax}"
  [[ -f "$root/experimental/termax_explore.py" ]] || root="$HOME/.local/share/termax"
  [[ -f "$root/experimental/termax_explore.py" ]] || { print -u2 "TERMAX Explorer sidecar not found"; return 127; }
  command python "$root/experimental/termax_explore.py" "$@"
}
txp() {
  local root="${TERMAX_REPO:-$HOME/termax}"
  [[ -f "$root/experimental/termax_pulse.py" ]] || root="$HOME/.local/share/termax"
  [[ -f "$root/experimental/termax_pulse.py" ]] || { print -u2 "TERMAX Pulse sidecar not found"; return 127; }
  command python "$root/experimental/termax_pulse.py" "$@"
}
alias txv='tx dashboard'

# Small conveniences
alias ports='ss -tulpen 2>/dev/null || netstat -tulpen 2>/dev/null'
alias myip='ip -brief address 2>/dev/null'
alias path='print -l \${(s.:.)PATH}'
alias reloadz='source ~/.zshrc'
alias week='date +%V'
alias now='date "+%Y-%m-%d %H:%M:%S"'

extract() {
  [[ -f "$1" ]] || { print -u2 "Usage: extract archive"; return 2; }
  case "$1" in
    *.tar.gz|*.tgz) tar -xzf "$1" ;;
    *.tar.xz) tar -xJf "$1" ;;
    *.tar.bz2) tar -xjf "$1" ;;
    *.tar) tar -xf "$1" ;;
    *.zip) unzip "$1" ;;
    *.gz) gunzip "$1" ;;
    *.7z) 7z x "$1" ;;
    *) print -u2 "Unsupported archive: $1"; return 2 ;;
  esac
}
