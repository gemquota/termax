#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PACKAGE_FILE="$ROOT/config/debian-packages.txt"
PYTHON_FILE="$ROOT/config/python-requirements.txt"
MODE="${1:-install}"
LOG="$HOME/termax-proot-bootstrap-$(date +%Y%m%d-%H%M%S).log"
FAILED=()
UNAVAILABLE=()
AVAILABLE=()

if [[ "$MODE" != "install" && "$MODE" != "check" && "$MODE" != "maintenance" ]]; then
  echo "Usage: proot-bootstrap.sh [install|check|maintenance]" >&2
  exit 2
fi
if [[ ! -f "$PACKAGE_FILE" || ! -f "$PYTHON_FILE" ]]; then
  echo "TERMAX Debian manifests are missing." >&2
  exit 2
fi
if [[ "${TERMAX_DEBUG:-0}" == "1" ]]; then set -x; fi
exec > >(tee -a "$LOG") 2>&1

echo
echo "============================================================"
echo " TERMAX Debian proot environment: $MODE"
echo " Log: $LOG"
echo "============================================================"

if [[ "$MODE" != "check" ]]; then
  echo "[1/5] Refreshing Debian package indexes..."
  if ! apt-get update; then FAILED+=("Debian apt update"); fi
  echo "[2/5] Upgrading installed Debian packages..."
  if ! apt-get upgrade -y; then FAILED+=("Debian apt upgrade"); fi
else
  echo "[1/5] Read-only Debian package inspection..."
fi

mapfile -t packages < <(sed -e 's/#.*//' -e '/^[[:space:]]*$/d' "$PACKAGE_FILE")
for package in "${packages[@]}"; do
  if apt-cache show "$package" >/dev/null 2>&1; then
    AVAILABLE+=("$package")
  else
    UNAVAILABLE+=("$package")
  fi
done

MISSING=()
for package in "${AVAILABLE[@]}"; do
  if ! dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q "install ok installed"; then
    MISSING+=("$package")
  fi
done
echo "Debian manifest: ${#packages[@]} | available: ${#AVAILABLE[@]} | unavailable in configured apt sources: ${#UNAVAILABLE[@]} | missing: ${#MISSING[@]}"
if (("${#MISSING[@]}" > 0)); then printf '  missing: %s\n' "${MISSING[*]}"; fi
if (("${#UNAVAILABLE[@]}" > 0)); then printf '  not packaged here: %s\n' "${UNAVAILABLE[*]}"; fi

if [[ "$MODE" == "check" ]]; then
  echo "Python environment: $HOME/.local/share/termax/venv"
  echo "Zsh stack: Oh My Zsh, Powerlevel10k, autosuggestions, syntax-highlighting, autocomplete, history-substring-search"
  echo "READ-ONLY: no packages or files were changed."
  exit 0
fi

if (("${#MISSING[@]}" > 0)); then
  echo "[3/5] Installing available Debian packages..."
  if ! apt-get install -y --no-install-recommends "${MISSING[@]}"; then
    echo "Package batch failed; retrying each available Debian package separately..."
    for package in "${MISSING[@]}"; do
      if ! apt-get install -y --no-install-recommends "$package"; then
        FAILED+=("Debian package: $package")
      fi
    done
  fi
else
  echo "[3/5] Debian package manifest already satisfied."
fi

echo "[4/5] Creating/updating TERMAX's isolated Debian Python environment..."
VENV="$HOME/.local/share/termax/venv"
mkdir -p "$(dirname "$VENV")"
if [[ ! -x "$VENV/bin/python" ]]; then
  if ! python3 -m venv "$VENV"; then
    FAILED+=("create Debian TERMAX Python venv")
  fi
fi
if [[ -x "$VENV/bin/python" ]]; then
  if ! "$VENV/bin/python" -m pip install --upgrade pip; then
    FAILED+=("Debian TERMAX pip upgrade")
  fi
  if ! "$VENV/bin/python" -m pip install -r "$PYTHON_FILE"; then
    FAILED+=("Debian Python requirements")
  fi
fi

echo "[5/5] Installing/configuring Debian Zsh, Oh My Zsh, Powerlevel10k and plugins..."
if ! command -v zsh >/dev/null 2>&1; then
  FAILED+=("Debian zsh package unavailable")
else
  OMZ="$HOME/.oh-my-zsh"
  if [[ ! -d "$OMZ" ]]; then
    RUNZSH=no CHSH=no KEEP_ZSHRC=yes sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" || FAILED+=("Debian Oh My Zsh")
  fi
  CUSTOM="${ZSH_CUSTOM:-$OMZ/custom}"
  mkdir -p "$CUSTOM/themes" "$CUSTOM/plugins"
  clone_plugin() {
    local repo="$1" dest="$2"
    if [[ -d "$dest/.git" ]]; then
      git -C "$dest" pull --ff-only || FAILED+=("update $dest")
    elif [[ ! -e "$dest" ]]; then
      git clone --depth=1 "$repo" "$dest" || FAILED+=("install $dest")
    fi
  }
  clone_plugin https://github.com/romkatv/powerlevel10k.git "$CUSTOM/themes/powerlevel10k"
  clone_plugin https://github.com/zsh-users/zsh-autosuggestions.git "$CUSTOM/plugins/zsh-autosuggestions"
  clone_plugin https://github.com/zsh-users/zsh-syntax-highlighting.git "$CUSTOM/plugins/zsh-syntax-highlighting"
  clone_plugin https://github.com/marlonrichert/zsh-autocomplete.git "$CUSTOM/plugins/zsh-autocomplete"
  clone_plugin https://github.com/zsh-users/zsh-history-substring-search.git "$CUSTOM/plugins/zsh-history-substring-search"

  ZRC="$HOME/.zshrc"
  if [[ ! -f "$ZRC" ]]; then
    if [[ -f "$OMZ/templates/zshrc.zsh-template" ]]; then
      cp "$OMZ/templates/zshrc.zsh-template" "$ZRC"
    else
      printf 'export ZSH="$HOME/.oh-my-zsh"\n' > "$ZRC"
    fi
  fi
  python3 - "$ZRC" <<'PY'
from pathlib import Path
import re, sys, time
path = Path(sys.argv[1])
original = path.read_text(encoding="utf-8")
text = original
theme = 'ZSH_THEME="powerlevel10k/powerlevel10k"'
plugins = 'plugins=(git zsh-autosuggestions zsh-syntax-highlighting zsh-autocomplete zsh-history-substring-search colored-man-pages)'
source_pattern = r'(?m)^\s*source\s+["\']?\$ZSH/oh-my-zsh\.sh["\']?\s*$'
if not re.search(r'(?m)^\s*export\s+ZSH=', text):
    text = 'export ZSH="$HOME/.oh-my-zsh"\n' + text
def set_before_omz(line, pattern):
    global text
    if re.search(pattern, text):
        text = re.sub(pattern, lambda _: line, text, count=1)
    else:
        found = re.search(source_pattern, text)
        if found:
            text = text[:found.start()] + line + "\n" + text[found.start():]
        else:
            text += "\n" + line + "\n"
set_before_omz(theme, r'(?m)^\s*ZSH_THEME=.*$')
set_before_omz(plugins, r'(?m)^\s*plugins=\(.*\)\s*$')
if not re.search(source_pattern, text):
    text += '\nsource "$ZSH/oh-my-zsh.sh"\n'
if "TERMAX_MANAGED_ZSH" not in text:
    text += "\n# TERMAX_MANAGED_ZSH\n"
if 'export PATH="$HOME/.local/bin:$PATH"' not in text:
    text += 'export PATH="$HOME/.local/bin:$PATH"\n'
if 'source "$HOME/.p10k.zsh"' not in text and 'source ~/.p10k.zsh' not in text:
    text += '[[ -f "$HOME/.p10k.zsh" ]] && source "$HOME/.p10k.zsh"\n'
if text != original:
    backup = path.with_name(path.name + ".termax-backup-" + time.strftime("%Y%m%d-%H%M%S"))
    backup.write_text(original, encoding="utf-8")
    print(f"  Backed up previous Zsh config: {backup}")
    path.write_text(text, encoding="utf-8")
PY  if [[ ! -f "$HOME/.p10k.zsh" && -f "$CUSTOM/themes/powerlevel10k/config/p10k-lean.zsh" ]]; then
    cp "$CUSTOM/themes/powerlevel10k/config/p10k-lean.zsh" "$HOME/.p10k.zsh"
  fi
fi

if (("${#UNAVAILABLE[@]}" > 0)); then
  echo "NOTE: Some Termux tools have no package under the same name in this Debian apt configuration."
fi
if (("${#FAILED[@]}" > 0)); then
  printf 'FAILED: %s\n' "${FAILED[*]}"
  exit 1
fi
echo "Debian proot environment bootstrap complete."
echo "WW's existing repository, virtualenv and cookies were not modified."
echo "No login shell was changed."
