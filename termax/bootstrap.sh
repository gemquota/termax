#!/data/data/com.termux/files/usr/bin/bash
set -uo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PKG_FILE="$ROOT/../config/termux-packages.txt"
PY_FILE="$ROOT/../config/python-requirements.txt"
LOG="$HOME/termax-bootstrap-$(date +%Y%m%d-%H%M%S).log"
FAILED=()

if [[ ! -d "${PREFIX:-}" || ! -x "${PREFIX:-/nonexistent}/bin/pkg" ]]; then
  echo "ERROR: Run this bootstrap inside native Termux." >&2
  exit 1
fi
if [[ ! -f "$PKG_FILE" || ! -f "$PY_FILE" ]]; then
  echo "ERROR: TERMAX manifests are missing." >&2
  exit 1
fi
if [[ "${TERMAX_DEBUG:-0}" == "1" ]]; then set -x; fi
exec > >(tee -a "$LOG") 2>&1

echo "TERMAX environment bootstrap"
echo "Termux: ${TERMUX_VERSION:-unknown} | Android: $(uname -m)"
echo "Log: $LOG"

mapfile -t packages < <(sed -e 's/#.*//' -e '/^[[:space:]]*$/d' "$PKG_FILE")
if [[ "${TERMAX_MINIMAL:-0}" == "1" ]]; then
  minimal=(bash ca-certificates curl git python python-pip zsh zsh-completions fzf ripgrep fd jq)
  filtered=()
  for package in "${packages[@]}"; do
    for keep in "${minimal[@]}"; do
      if [[ "$package" == "$keep" ]]; then filtered+=("$package"); break; fi
    done
  done
  packages=("${filtered[@]}")
  echo "Minimal package profile selected."
fi

echo "Updating Termux package indexes..."
if ! pkg update -y; then echo "ERROR: pkg update failed"; exit 1; fi
if ! pkg upgrade -y; then echo "ERROR: pkg upgrade failed"; exit 1; fi

echo "Installing ${#packages[@]} explicitly requested Termux packages..."
for package in "${packages[@]}"; do
  if dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q "install ok installed"; then
    echo "[already installed] $package"
    continue
  fi
  echo "[install] $package"
  if ! pkg install -y "$package"; then
    FAILED+=("$package")
    echo "[FAILED] $package"
  fi
done

echo "Installing Python dependencies..."
if [[ "${TERMAX_MINIMAL:-0}" == "1" ]]; then
  if ! python -m pip install --upgrade pip rich; then FAILED+=("minimal Python requirements"); fi
else
  if ! python -m pip install --upgrade pip; then FAILED+=("pip upgrade"); fi
  if ! python -m pip install -r "$PY_FILE"; then FAILED+=("Python requirements"); fi
fi

HAD_ZSHRC=0
[[ -f "$HOME/.zshrc" ]] && HAD_ZSHRC=1
echo "Installing Oh My Zsh..."
if [[ ! -d "$HOME/.oh-my-zsh" ]]; then
  RUNZSH=no CHSH=no KEEP_ZSHRC=yes sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" || {
    echo "ERROR: Oh My Zsh installation failed"; exit 1;
  }
else
  echo "Oh My Zsh already exists; leaving it in place."
fi

ZSH_CUSTOM="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"
mkdir -p "$ZSH_CUSTOM/plugins" "$ZSH_CUSTOM/themes"
clone_plugin() {
  local repo="$1" dest="$2"
  if [[ -d "$dest/.git" ]]; then
    git -C "$dest" pull --ff-only || echo "WARNING: Could not update $dest"
  elif [[ ! -e "$dest" ]]; then
    git clone --depth=1 "$repo" "$dest" || echo "WARNING: Could not clone $repo"
  fi
}
clone_plugin https://github.com/romkatv/powerlevel10k.git "$ZSH_CUSTOM/themes/powerlevel10k"
clone_plugin https://github.com/zsh-users/zsh-autosuggestions.git "$ZSH_CUSTOM/plugins/zsh-autosuggestions"
clone_plugin https://github.com/zsh-users/zsh-syntax-highlighting.git "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting"
clone_plugin https://github.com/marlonrichert/zsh-autocomplete.git "$ZSH_CUSTOM/plugins/zsh-autocomplete"
clone_plugin https://github.com/zsh-users/zsh-history-substring-search.git "$ZSH_CUSTOM/plugins/zsh-history-substring-search"

ZRC="$HOME/.zshrc"
if (( HAD_ZSHRC == 0 )); then
  sed -i 's|^[[:space:]]*ZSH_THEME=.*|ZSH_THEME="powerlevel10k/powerlevel10k"|' "$ZRC"
  sed -i 's|^[[:space:]]*plugins=.*|plugins=(git zsh-autosuggestions zsh-syntax-highlighting zsh-autocomplete zsh-history-substring-search colored-man-pages)|' "$ZRC"
  if ! grep -q 'TERMAX_MANAGED_ZSH' "$ZRC"; then
    cat >> "$ZRC" <<'EOF'

# TERMAX_MANAGED_ZSH: managed additions.
export PATH="$HOME/.local/bin:$PATH"
[[ -f "$HOME/.p10k.zsh" ]] && source "$HOME/.p10k.zsh"
EOF
  fi
else
  cp -p "$ZRC" "$ZRC.termax-backup-$(date +%Y%m%d-%H%M%S)"
  if ! grep -q 'TERMAX_MANAGED_ZSH' "$ZRC"; then
    cat >> "$ZRC" <<'EOF'

# TERMAX_MANAGED_ZSH: managed additions; remove this block to disable.
export PATH="$HOME/.local/bin:$PATH"
EOF
  fi
  echo "Existing .zshrc backed up and preserved; theme/plugin settings were not overwritten."
fi

mkdir -p "$HOME/.local/bin"
if (("${#FAILED[@]}" > 0)); then
  echo "Bootstrap completed with failures: ${FAILED[*]}"
  echo "Review the log: $LOG"
  exit 1
fi
echo "Bootstrap complete."
echo "No login-shell change was made. Review your shell settings before changing the login shell."
echo "Termux:API also requires the separate Android Termux:API companion app."
