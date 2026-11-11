#!/data/data/com.termux/files/usr/bin/bash
set -uo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PKG_FILE="$ROOT/config/termux-packages.txt"
PY_FILE="$ROOT/config/python-requirements.txt"
LOG="$HOME/termax-bootstrap-$(date +%Y%m%d-%H%M%S).log"

if [[ ! -d "${PREFIX:-}" || ! -x "${PREFIX:-/nonexistent}/bin/pkg" ]]; then
  echo "ERROR: Run this installer inside Termux." >&2
  exit 1
fi
if [[ ! -f "$PKG_FILE" || ! -f "$PY_FILE" ]]; then
  echo "ERROR: Missing package manifests in $ROOT/config" >&2
  exit 1
fi

exec > >(tee -a "$LOG") 2>&1
echo "TERMAX environment bootstrap"
echo "Termux: ${TERMUX_VERSION:-unknown} | Android: $(uname -m)"
echo "Log: $LOG"

mapfile -t packages < <(sed -e 's/#.*//' -e '/^[[:space:]]*$/d' "$PKG_FILE")
echo
echo "Updating Termux package indexes..."
pkg update -y || { echo "ERROR: pkg update failed"; exit 1; }
pkg upgrade -y || echo "WARNING: pkg upgrade reported a failure; continuing."

echo
echo "Installing ${#packages[@]} explicitly requested Termux packages..."
failed=()
for package in "${packages[@]}"; do
  if dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q "install ok installed"; then
    echo "[already installed] $package"
    continue
  fi
  echo "[install] $package"
  if ! pkg install -y "$package"; then
    failed+=("$package")
    echo "[FAILED] $package"
  fi
done

echo
echo "Installing Python dependencies..."
python -m pip install --upgrade pip
if ! python -m pip install -r "$PY_FILE"; then
  echo "WARNING: Python dependency installation reported errors."
  python -m pip check || true
fi

echo
echo "Installing Oh My Zsh..."
if [[ ! -d "$HOME/.oh-my-zsh" ]]; then
  RUNZSH=no CHSH=no KEEP_ZSHRC=yes     sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" || {
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
if [[ ! -f "$ZRC" ]]; then
  cat > "$ZRC" <<'EOF'
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="powerlevel10k/powerlevel10k"
plugins=(git zsh-autosuggestions zsh-syntax-highlighting zsh-autocomplete zsh-history-substring-search colored-man-pages)
source "$ZSH/oh-my-zsh.sh"
[[ -f "$HOME/.p10k.zsh" ]] && source "$HOME/.p10k.zsh"
EOF
else
  cp -p "$ZRC" "$ZRC.termax-backup-$(date +%Y%m%d-%H%M%S)"
  if ! grep -q 'TERMAX_MANAGED_ZSH' "$ZRC"; then
    cat >> "$ZRC" <<'EOF'

# TERMAX_MANAGED_ZSH: managed additions; remove this block to disable.
export PATH="$HOME/.local/bin:$PATH"
EOF
  fi
  echo "Existing .zshrc preserved; no theme or plugin settings overwritten."
fi

mkdir -p "$HOME/.local/bin"
if command -v zsh >/dev/null 2>&1; then
  chsh -s "$(command -v zsh)" || echo "WARNING: Could not set login shell automatically."
fi

echo
echo "Bootstrap complete."
if (("${#failed[@]}" > 0)); then
  echo "Packages not installed: ${failed[*]}"
  echo "Check repository availability and the log: $LOG"
else
  echo "All manifest Termux packages installed."
fi
echo "Run: bash "$ROOT/audit-termux.sh""
echo "Then close and reopen Termux, or run: exec zsh"
echo "Termux:API also requires the separate Android Termux:API companion app."
