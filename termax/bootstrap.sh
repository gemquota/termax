#!/data/data/com.termux/files/usr/bin/bash
set -uo pipefail

APP_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PKG_FILE="$APP_ROOT/config/termux-packages.txt"
PY_FILE="$APP_ROOT/config/python-requirements.txt"
PROOT_SCRIPT="$APP_ROOT/termax/proot-bootstrap.sh"
LOG="$HOME/termax-bootstrap-$(date +%Y%m%d-%H%M%S).log"
FAILED=()

if [[ ! -d "${PREFIX:-}" || ! -x "${PREFIX:-/nonexistent}/bin/pkg" ]]; then
  echo "ERROR: Run this bootstrap inside native Termux." >&2
  exit 1
fi
for required in "$PKG_FILE" "$PY_FILE" "$PROOT_SCRIPT"; do
  if [[ ! -f "$required" ]]; then echo "ERROR: Missing bootstrap component: $required" >&2; exit 1; fi
done
if [[ "${TERMAX_DEBUG:-0}" == "1" ]]; then set -x; fi
exec > >(tee -a "$LOG") 2>&1

echo
echo "============================================================"
echo " TERMAX full environment bootstrap"
echo " Native Termux + Debian proot"
echo " Log: $LOG"
echo "============================================================"

mapfile -t packages < <(sed -e 's/#.*//' -e '/^[[:space:]]*$/d' "$PKG_FILE")
if [[ "${TERMAX_MINIMAL:-0}" == "1" ]]; then
  minimal=(bash ca-certificates curl git python python-pip proot-distro zsh zsh-completions fzf ripgrep fd jq)
  filtered=()
  for package in "${packages[@]}"; do
    for keep in "${minimal[@]}"; do
      if [[ "$package" == "$keep" ]]; then filtered+=("$package"); break; fi
    done
  done
  packages=("${filtered[@]}")
  echo "Minimal package profile selected."
fi

echo
echo "[1/6] Updating native Termux..."
if ! pkg update -y; then echo "ERROR: pkg update failed"; exit 1; fi
if ! pkg upgrade -y; then echo "ERROR: pkg upgrade failed"; exit 1; fi

echo
echo "[2/6] Installing native Termux packages (${#packages[@]} requested)..."
for package in "${packages[@]}"; do
  if dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q "install ok installed"; then
    echo "  [present] $package"
    continue
  fi
  echo "  [install] $package"
  if ! pkg install -y "$package"; then
    FAILED+=("Termux package: $package")
    echo "  [FAILED] $package"
  fi
done

echo
echo "[3/6] Installing native Termux Python requirements..."
if [[ "${TERMAX_MINIMAL:-0}" == "1" ]]; then
  if ! python -m pip install --upgrade pip rich; then FAILED+=("Termux minimal Python requirements"); fi
else
  if ! python -m pip install --upgrade pip; then FAILED+=("Termux pip upgrade"); fi
  if ! python -m pip install -r "$PY_FILE"; then FAILED+=("Termux Python requirements"); fi
fi

echo
echo "[4/6] Installing native Termux Zsh, Oh My Zsh, Powerlevel10k and plugins..."
OMZ="$HOME/.oh-my-zsh"
if [[ ! -d "$OMZ" ]]; then
  RUNZSH=no CHSH=no KEEP_ZSHRC=yes sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" || FAILED+=("Termux Oh My Zsh")
else
  echo "  Oh My Zsh already exists."
fi
CUSTOM="${ZSH_CUSTOM:-$OMZ/custom}"
mkdir -p "$CUSTOM/plugins" "$CUSTOM/themes"
clone_plugin() {
  local repo="$1" dest="$2"
  if [[ -d "$dest/.git" ]]; then
    git -C "$dest" pull --ff-only || FAILED+=("update $dest")
  elif [[ ! -e "$dest" ]]; then
    git clone --depth=1 "$repo" "$dest" || FAILED+=("install $dest")
  else
    echo "  [preserved] $dest exists but is not a Git checkout."
  fi
}
clone_plugin https://github.com/romkatv/powerlevel10k.git "$CUSTOM/themes/powerlevel10k"
clone_plugin https://github.com/zsh-users/zsh-autosuggestions.git "$CUSTOM/plugins/zsh-autosuggestions"
clone_plugin https://github.com/zsh-users/zsh-syntax-highlighting.git "$CUSTOM/plugins/zsh-syntax-highlighting"
clone_plugin https://github.com/marlonrichert/zsh-autocomplete.git "$CUSTOM/plugins/zsh-autocomplete"
clone_plugin https://github.com/zsh-users/zsh-history-substring-search.git "$CUSTOM/plugins/zsh-history-substring-search"

ZRC="$HOME/.zshrc"
if [[ ! -f "$ZRC" ]]; then
  if [[ -f "$OMZ/templates/zshrc.zsh-template" ]]; then cp "$OMZ/templates/zshrc.zsh-template" "$ZRC"
  else printf 'export ZSH="$HOME/.oh-my-zsh"\n' > "$ZRC"; fi
fi
python - "$ZRC" <<'PY'
from pathlib import Path
import re, sys
path = Path(sys.argv[1])
original = path.read_text(encoding="utf-8")
text = original
theme = 'ZSH_THEME="powerlevel10k/powerlevel10k"'
managed_plugins = ["zsh-autosuggestions", "zsh-syntax-highlighting", "zsh-autocomplete",
                   "zsh-history-substring-search", "colored-man-pages"]
source_pattern = r'(?m)^\s*source\s+["\']?\$ZSH/oh-my-zsh\.sh["\']?\s*
if not re.search(source_pattern, text):
    text += '\nsource "$ZSH/oh-my-zsh.sh"\n'
if "TERMAX_MANAGED_ZSH" not in text:
    text += "\n# TERMAX_MANAGED_ZSH\n"
if 'export PATH="$HOME/.local/bin:$PATH"' not in text:
    text += 'export PATH="$HOME/.local/bin:$PATH"\n'
if 'source "$HOME/.p10k.zsh"' not in text and 'source ~/.p10k.zsh' not in text:
    text += '[[ -f "$HOME/.p10k.zsh" ]] && source "$HOME/.p10k.zsh"\n'
if text != original:
    if path.exists() and original:
        import time
        backup = path.with_name(path.name + ".termax-backup-" + time.strftime("%Y%m%d-%H%M%S"))
        if backup.exists():
            backup = backup.with_name(backup.name + "-" + str(time.time_ns()))
        backup.write_text(original, encoding="utf-8")
        print(f"  Backed up previous Zsh config: {backup}")
    path.write_text(text, encoding="utf-8")
PY
if [[ ! -f "$HOME/.p10k.zsh" && -f "$CUSTOM/themes/powerlevel10k/config/p10k-lean.zsh" ]]; then
  cp "$CUSTOM/themes/powerlevel10k/config/p10k-lean.zsh" "$HOME/.p10k.zsh"
fi
mkdir -p "$HOME/.local/bin"

echo
echo "[5/6] Ensuring the existing Debian proot is available..."
if ! command -v proot-distro >/dev/null 2>&1; then
  FAILED+=("proot-distro command unavailable")
elif ! proot-distro login debian -- /bin/true >/dev/null 2>&1; then
  echo "  Debian distribution not found; installing it without touching other distributions..."
  if ! proot-distro install debian; then
    FAILED+=("install Debian proot distribution")
  fi
fi

if command -v proot-distro >/dev/null 2>&1 && proot-distro login debian -- /bin/true >/dev/null 2>&1; then
  echo
  echo "[6/6] Installing Debian proot packages, Python environment and Zsh stack..."
  PROOT_ARGS=(login debian --bind "$APP_ROOT:/mnt/termax-source" -- /usr/bin/env)
  if [[ "${TERMAX_DEBUG:-0}" == "1" ]]; then PROOT_ARGS+=(TERMAX_DEBUG=1); fi
  if [[ "${TERMAX_MINIMAL:-0}" == "1" ]]; then PROOT_ARGS+=(TERMAX_MINIMAL=1); fi
  PROOT_ARGS+=(/bin/bash --noprofile --norc /mnt/termax-source/termax/proot-bootstrap.sh install)
  proot-distro "${PROOT_ARGS[@]}" || FAILED+=("Debian proot bootstrap")
else
  FAILED+=("Debian proot unavailable; WW was left untouched")
fi


echo
echo "Final native Termux audit..."
FINAL_MISSING=()
for package in "${packages[@]}"; do
  if ! dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q "install ok installed"; then
    FINAL_MISSING+=("$package")
  fi
done
if (("${#FINAL_MISSING[@]}" > 0)); then
  printf '  Missing native packages: %s\n' "${FINAL_MISSING[*]}"
  FAILED+=("native Termux final package audit")
fi
if [[ "${TERMAX_MINIMAL:-0}" == "1" ]]; then
  modules=(rich)
else
  modules=(rich cloudscraper fastapi httplib2 opentelemetry requests requests_toolbelt uvicorn textual prompt_toolkit plotext networkx yaml typer)
fi
for module in "${modules[@]}"; do
  if ! python -c "import $module" >/dev/null 2>&1; then FAILED+=("native Python module: $module"); fi
done
if command -v zsh >/dev/null 2>&1; then
  [[ -d "$HOME/.oh-my-zsh" ]] || FAILED+=("native Oh My Zsh")
  [[ -f "$HOME/.zshrc" ]] || FAILED+=("native .zshrc")
  [[ -f "$HOME/.p10k.zsh" ]] || FAILED+=("native .p10k.zsh")
  [[ -f "$CUSTOM/themes/powerlevel10k/powerlevel10k.zsh-theme" ]] || FAILED+=("native Powerlevel10k")
  [[ -f "$CUSTOM/plugins/zsh-autosuggestions/zsh-autosuggestions.plugin.zsh" ]] || FAILED+=("native zsh-autosuggestions")
  [[ -f "$CUSTOM/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh" ]] || FAILED+=("native zsh-syntax-highlighting")
  [[ -f "$CUSTOM/plugins/zsh-autocomplete/zsh-autocomplete.plugin.zsh" ]] || FAILED+=("native zsh-autocomplete")
  [[ -f "$CUSTOM/plugins/zsh-history-substring-search/zsh-history-substring-search.zsh" ]] || FAILED+=("native zsh-history-substring-search")
  zsh -n "$HOME/.zshrc" || FAILED+=("native .zshrc syntax")
else
  FAILED+=("native zsh executable missing")
fi
echo
if (("${#FAILED[@]}" > 0)); then
  echo "TERMAX bootstrap completed with failures:"
  printf '  - %s\n' "${FAILED[@]}"
  echo "Review native log: $LOG"
  exit 1
fi
echo "TERMAX native Termux + Debian proot bootstrap complete."
echo "Zsh/Oh My Zsh/Powerlevel10k are installed in both environments."
echo "Existing .zshrc files were backed up before TERMAX changes."
echo "WW's repository, virtualenv and cookies were not modified."
echo "No login shell was changed automatically."
echo "Termux:API also requires the separate Android companion app and permissions."

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
set_before_omz(theme, r'(?m)^\s*ZSH_THEME=.*
if not re.search(source_pattern, text):
    text += '\nsource "$ZSH/oh-my-zsh.sh"\n'
if "TERMAX_MANAGED_ZSH" not in text:
    text += "\n# TERMAX_MANAGED_ZSH\n"
if 'export PATH="$HOME/.local/bin:$PATH"' not in text:
    text += 'export PATH="$HOME/.local/bin:$PATH"\n'
if 'source "$HOME/.p10k.zsh"' not in text and 'source ~/.p10k.zsh' not in text:
    text += '[[ -f "$HOME/.p10k.zsh" ]] && source "$HOME/.p10k.zsh"\n'
if text != original:
    if path.exists() and original:
        import time
        backup = path.with_name(path.name + ".termax-backup-" + time.strftime("%Y%m%d-%H%M%S"))
        backup.write_text(original, encoding="utf-8")
        print(f"  Backed up previous Zsh config: {backup}")
    path.write_text(text, encoding="utf-8")
PY
if [[ ! -f "$HOME/.p10k.zsh" && -f "$CUSTOM/themes/powerlevel10k/config/p10k-lean.zsh" ]]; then
  cp "$CUSTOM/themes/powerlevel10k/config/p10k-lean.zsh" "$HOME/.p10k.zsh"
fi
mkdir -p "$HOME/.local/bin"

echo
echo "[5/6] Ensuring the existing Debian proot is available..."
if ! command -v proot-distro >/dev/null 2>&1; then
  FAILED+=("proot-distro command unavailable")
elif ! proot-distro login debian -- /bin/true >/dev/null 2>&1; then
  echo "  Debian distribution not found; installing it without touching other distributions..."
  if ! proot-distro install debian; then
    FAILED+=("install Debian proot distribution")
  fi
fi

if command -v proot-distro >/dev/null 2>&1 && proot-distro login debian -- /bin/true >/dev/null 2>&1; then
  echo
  echo "[6/6] Installing Debian proot packages, Python environment and Zsh stack..."
  PROOT_ARGS=(login debian --bind "$APP_ROOT:/mnt/termax-source" -- /usr/bin/env)
  if [[ "${TERMAX_DEBUG:-0}" == "1" ]]; then PROOT_ARGS+=(TERMAX_DEBUG=1); fi
  if [[ "${TERMAX_MINIMAL:-0}" == "1" ]]; then PROOT_ARGS+=(TERMAX_MINIMAL=1); fi
  PROOT_ARGS+=(/bin/bash --noprofile --norc /mnt/termax-source/termax/proot-bootstrap.sh install)
  proot-distro "${PROOT_ARGS[@]}" || FAILED+=("Debian proot bootstrap")
else
  FAILED+=("Debian proot unavailable; WW was left untouched")
fi


echo
echo "Final native Termux audit..."
FINAL_MISSING=()
for package in "${packages[@]}"; do
  if ! dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q "install ok installed"; then
    FINAL_MISSING+=("$package")
  fi
done
if (("${#FINAL_MISSING[@]}" > 0)); then
  printf '  Missing native packages: %s\n' "${FINAL_MISSING[*]}"
  FAILED+=("native Termux final package audit")
fi
if [[ "${TERMAX_MINIMAL:-0}" == "1" ]]; then
  modules=(rich)
else
  modules=(rich cloudscraper fastapi httplib2 opentelemetry requests requests_toolbelt uvicorn textual prompt_toolkit plotext networkx yaml typer)
fi
for module in "${modules[@]}"; do
  if ! python -c "import $module" >/dev/null 2>&1; then FAILED+=("native Python module: $module"); fi
done
if command -v zsh >/dev/null 2>&1; then
  [[ -d "$HOME/.oh-my-zsh" ]] || FAILED+=("native Oh My Zsh")
  [[ -f "$HOME/.zshrc" ]] || FAILED+=("native .zshrc")
  [[ -f "$HOME/.p10k.zsh" ]] || FAILED+=("native .p10k.zsh")
  [[ -f "$CUSTOM/themes/powerlevel10k/powerlevel10k.zsh-theme" ]] || FAILED+=("native Powerlevel10k")
  [[ -f "$CUSTOM/plugins/zsh-autosuggestions/zsh-autosuggestions.plugin.zsh" ]] || FAILED+=("native zsh-autosuggestions")
  [[ -f "$CUSTOM/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh" ]] || FAILED+=("native zsh-syntax-highlighting")
  [[ -f "$CUSTOM/plugins/zsh-autocomplete/zsh-autocomplete.plugin.zsh" ]] || FAILED+=("native zsh-autocomplete")
  [[ -f "$CUSTOM/plugins/zsh-history-substring-search/zsh-history-substring-search.zsh" ]] || FAILED+=("native zsh-history-substring-search")
  zsh -n "$HOME/.zshrc" || FAILED+=("native .zshrc syntax")
else
  FAILED+=("native zsh executable missing")
fi
echo
if (("${#FAILED[@]}" > 0)); then
  echo "TERMAX bootstrap completed with failures:"
  printf '  - %s\n' "${FAILED[@]}"
  echo "Review native log: $LOG"
  exit 1
fi
echo "TERMAX native Termux + Debian proot bootstrap complete."
echo "Zsh/Oh My Zsh/Powerlevel10k are installed in both environments."
echo "Existing .zshrc files were backed up before TERMAX changes."
echo "WW's repository, virtualenv and cookies were not modified."
echo "No login shell was changed automatically."
echo "Termux:API also requires the separate Android companion app and permissions."
)
match = re.search(r'(?m)^\s*plugins=\(([^)]*)\)\s*
if not re.search(source_pattern, text):
    text += '\nsource "$ZSH/oh-my-zsh.sh"\n'
if "TERMAX_MANAGED_ZSH" not in text:
    text += "\n# TERMAX_MANAGED_ZSH\n"
if 'export PATH="$HOME/.local/bin:$PATH"' not in text:
    text += 'export PATH="$HOME/.local/bin:$PATH"\n'
if 'source "$HOME/.p10k.zsh"' not in text and 'source ~/.p10k.zsh' not in text:
    text += '[[ -f "$HOME/.p10k.zsh" ]] && source "$HOME/.p10k.zsh"\n'
if text != original:
    if path.exists() and original:
        import time
        backup = path.with_name(path.name + ".termax-backup-" + time.strftime("%Y%m%d-%H%M%S"))
        backup.write_text(original, encoding="utf-8")
        print(f"  Backed up previous Zsh config: {backup}")
    path.write_text(text, encoding="utf-8")
PY
if [[ ! -f "$HOME/.p10k.zsh" && -f "$CUSTOM/themes/powerlevel10k/config/p10k-lean.zsh" ]]; then
  cp "$CUSTOM/themes/powerlevel10k/config/p10k-lean.zsh" "$HOME/.p10k.zsh"
fi
mkdir -p "$HOME/.local/bin"

echo
echo "[5/6] Ensuring the existing Debian proot is available..."
if ! command -v proot-distro >/dev/null 2>&1; then
  FAILED+=("proot-distro command unavailable")
elif ! proot-distro login debian -- /bin/true >/dev/null 2>&1; then
  echo "  Debian distribution not found; installing it without touching other distributions..."
  if ! proot-distro install debian; then
    FAILED+=("install Debian proot distribution")
  fi
fi

if command -v proot-distro >/dev/null 2>&1 && proot-distro login debian -- /bin/true >/dev/null 2>&1; then
  echo
  echo "[6/6] Installing Debian proot packages, Python environment and Zsh stack..."
  PROOT_ARGS=(login debian --bind "$APP_ROOT:/mnt/termax-source" -- /usr/bin/env)
  if [[ "${TERMAX_DEBUG:-0}" == "1" ]]; then PROOT_ARGS+=(TERMAX_DEBUG=1); fi
  if [[ "${TERMAX_MINIMAL:-0}" == "1" ]]; then PROOT_ARGS+=(TERMAX_MINIMAL=1); fi
  PROOT_ARGS+=(/bin/bash --noprofile --norc /mnt/termax-source/termax/proot-bootstrap.sh install)
  proot-distro "${PROOT_ARGS[@]}" || FAILED+=("Debian proot bootstrap")
else
  FAILED+=("Debian proot unavailable; WW was left untouched")
fi


echo
echo "Final native Termux audit..."
FINAL_MISSING=()
for package in "${packages[@]}"; do
  if ! dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q "install ok installed"; then
    FINAL_MISSING+=("$package")
  fi
done
if (("${#FINAL_MISSING[@]}" > 0)); then
  printf '  Missing native packages: %s\n' "${FINAL_MISSING[*]}"
  FAILED+=("native Termux final package audit")
fi
if [[ "${TERMAX_MINIMAL:-0}" == "1" ]]; then
  modules=(rich)
else
  modules=(rich cloudscraper fastapi httplib2 opentelemetry requests requests_toolbelt uvicorn textual prompt_toolkit plotext networkx yaml typer)
fi
for module in "${modules[@]}"; do
  if ! python -c "import $module" >/dev/null 2>&1; then FAILED+=("native Python module: $module"); fi
done
if command -v zsh >/dev/null 2>&1; then
  [[ -d "$HOME/.oh-my-zsh" ]] || FAILED+=("native Oh My Zsh")
  [[ -f "$HOME/.zshrc" ]] || FAILED+=("native .zshrc")
  [[ -f "$HOME/.p10k.zsh" ]] || FAILED+=("native .p10k.zsh")
  [[ -f "$CUSTOM/themes/powerlevel10k/powerlevel10k.zsh-theme" ]] || FAILED+=("native Powerlevel10k")
  [[ -f "$CUSTOM/plugins/zsh-autosuggestions/zsh-autosuggestions.plugin.zsh" ]] || FAILED+=("native zsh-autosuggestions")
  [[ -f "$CUSTOM/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh" ]] || FAILED+=("native zsh-syntax-highlighting")
  [[ -f "$CUSTOM/plugins/zsh-autocomplete/zsh-autocomplete.plugin.zsh" ]] || FAILED+=("native zsh-autocomplete")
  [[ -f "$CUSTOM/plugins/zsh-history-substring-search/zsh-history-substring-search.zsh" ]] || FAILED+=("native zsh-history-substring-search")
  zsh -n "$HOME/.zshrc" || FAILED+=("native .zshrc syntax")
else
  FAILED+=("native zsh executable missing")
fi
echo
if (("${#FAILED[@]}" > 0)); then
  echo "TERMAX bootstrap completed with failures:"
  printf '  - %s\n' "${FAILED[@]}"
  echo "Review native log: $LOG"
  exit 1
fi
echo "TERMAX native Termux + Debian proot bootstrap complete."
echo "Zsh/Oh My Zsh/Powerlevel10k are installed in both environments."
echo "Existing .zshrc files were backed up before TERMAX changes."
echo "WW's repository, virtualenv and cookies were not modified."
echo "No login shell was changed automatically."
echo "Termux:API also requires the separate Android companion app and permissions."
, text)
existing_plugins = match.group(1).split() if match else ["git"]
plugins = "plugins=(" + " ".join(dict.fromkeys(existing_plugins + managed_plugins)) + ")"
if match:
    text = text[:match.start()] + plugins + text[match.end():]
else:
    set_before_omz(plugins, r'(?m)^\s*plugins=\(.*\)\s*
if not re.search(source_pattern, text):
    text += '\nsource "$ZSH/oh-my-zsh.sh"\n'
if "TERMAX_MANAGED_ZSH" not in text:
    text += "\n# TERMAX_MANAGED_ZSH\n"
if 'export PATH="$HOME/.local/bin:$PATH"' not in text:
    text += 'export PATH="$HOME/.local/bin:$PATH"\n'
if 'source "$HOME/.p10k.zsh"' not in text and 'source ~/.p10k.zsh' not in text:
    text += '[[ -f "$HOME/.p10k.zsh" ]] && source "$HOME/.p10k.zsh"\n'
if text != original:
    if path.exists() and original:
        import time
        backup = path.with_name(path.name + ".termax-backup-" + time.strftime("%Y%m%d-%H%M%S"))
        backup.write_text(original, encoding="utf-8")
        print(f"  Backed up previous Zsh config: {backup}")
    path.write_text(text, encoding="utf-8")
PY
if [[ ! -f "$HOME/.p10k.zsh" && -f "$CUSTOM/themes/powerlevel10k/config/p10k-lean.zsh" ]]; then
  cp "$CUSTOM/themes/powerlevel10k/config/p10k-lean.zsh" "$HOME/.p10k.zsh"
fi
mkdir -p "$HOME/.local/bin"

echo
echo "[5/6] Ensuring the existing Debian proot is available..."
if ! command -v proot-distro >/dev/null 2>&1; then
  FAILED+=("proot-distro command unavailable")
elif ! proot-distro login debian -- /bin/true >/dev/null 2>&1; then
  echo "  Debian distribution not found; installing it without touching other distributions..."
  if ! proot-distro install debian; then
    FAILED+=("install Debian proot distribution")
  fi
fi

if command -v proot-distro >/dev/null 2>&1 && proot-distro login debian -- /bin/true >/dev/null 2>&1; then
  echo
  echo "[6/6] Installing Debian proot packages, Python environment and Zsh stack..."
  PROOT_ARGS=(login debian --bind "$APP_ROOT:/mnt/termax-source" -- /usr/bin/env)
  if [[ "${TERMAX_DEBUG:-0}" == "1" ]]; then PROOT_ARGS+=(TERMAX_DEBUG=1); fi
  if [[ "${TERMAX_MINIMAL:-0}" == "1" ]]; then PROOT_ARGS+=(TERMAX_MINIMAL=1); fi
  PROOT_ARGS+=(/bin/bash --noprofile --norc /mnt/termax-source/termax/proot-bootstrap.sh install)
  proot-distro "${PROOT_ARGS[@]}" || FAILED+=("Debian proot bootstrap")
else
  FAILED+=("Debian proot unavailable; WW was left untouched")
fi


echo
echo "Final native Termux audit..."
FINAL_MISSING=()
for package in "${packages[@]}"; do
  if ! dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q "install ok installed"; then
    FINAL_MISSING+=("$package")
  fi
done
if (("${#FINAL_MISSING[@]}" > 0)); then
  printf '  Missing native packages: %s\n' "${FINAL_MISSING[*]}"
  FAILED+=("native Termux final package audit")
fi
if [[ "${TERMAX_MINIMAL:-0}" == "1" ]]; then
  modules=(rich)
else
  modules=(rich cloudscraper fastapi httplib2 opentelemetry requests requests_toolbelt uvicorn textual prompt_toolkit plotext networkx yaml typer)
fi
for module in "${modules[@]}"; do
  if ! python -c "import $module" >/dev/null 2>&1; then FAILED+=("native Python module: $module"); fi
done
if command -v zsh >/dev/null 2>&1; then
  [[ -d "$HOME/.oh-my-zsh" ]] || FAILED+=("native Oh My Zsh")
  [[ -f "$HOME/.zshrc" ]] || FAILED+=("native .zshrc")
  [[ -f "$HOME/.p10k.zsh" ]] || FAILED+=("native .p10k.zsh")
  [[ -f "$CUSTOM/themes/powerlevel10k/powerlevel10k.zsh-theme" ]] || FAILED+=("native Powerlevel10k")
  [[ -f "$CUSTOM/plugins/zsh-autosuggestions/zsh-autosuggestions.plugin.zsh" ]] || FAILED+=("native zsh-autosuggestions")
  [[ -f "$CUSTOM/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh" ]] || FAILED+=("native zsh-syntax-highlighting")
  [[ -f "$CUSTOM/plugins/zsh-autocomplete/zsh-autocomplete.plugin.zsh" ]] || FAILED+=("native zsh-autocomplete")
  [[ -f "$CUSTOM/plugins/zsh-history-substring-search/zsh-history-substring-search.zsh" ]] || FAILED+=("native zsh-history-substring-search")
  zsh -n "$HOME/.zshrc" || FAILED+=("native .zshrc syntax")
else
  FAILED+=("native zsh executable missing")
fi
echo
if (("${#FAILED[@]}" > 0)); then
  echo "TERMAX bootstrap completed with failures:"
  printf '  - %s\n' "${FAILED[@]}"
  echo "Review native log: $LOG"
  exit 1
fi
echo "TERMAX native Termux + Debian proot bootstrap complete."
echo "Zsh/Oh My Zsh/Powerlevel10k are installed in both environments."
echo "Existing .zshrc files were backed up before TERMAX changes."
echo "WW's repository, virtualenv and cookies were not modified."
echo "No login shell was changed automatically."
echo "Termux:API also requires the separate Android companion app and permissions."
)
if not re.search(source_pattern, text):
    text += '\nsource "$ZSH/oh-my-zsh.sh"\n'
if "TERMAX_MANAGED_ZSH" not in text:
    text += "\n# TERMAX_MANAGED_ZSH\n"
if 'export PATH="$HOME/.local/bin:$PATH"' not in text:
    text += 'export PATH="$HOME/.local/bin:$PATH"\n'
if 'source "$HOME/.p10k.zsh"' not in text and 'source ~/.p10k.zsh' not in text:
    text += '[[ -f "$HOME/.p10k.zsh" ]] && source "$HOME/.p10k.zsh"\n'
if text != original:
    if path.exists() and original:
        import time
        backup = path.with_name(path.name + ".termax-backup-" + time.strftime("%Y%m%d-%H%M%S"))
        backup.write_text(original, encoding="utf-8")
        print(f"  Backed up previous Zsh config: {backup}")
    path.write_text(text, encoding="utf-8")
PY
if [[ ! -f "$HOME/.p10k.zsh" && -f "$CUSTOM/themes/powerlevel10k/config/p10k-lean.zsh" ]]; then
  cp "$CUSTOM/themes/powerlevel10k/config/p10k-lean.zsh" "$HOME/.p10k.zsh"
fi
mkdir -p "$HOME/.local/bin"

echo
echo "[5/6] Ensuring the existing Debian proot is available..."
if ! command -v proot-distro >/dev/null 2>&1; then
  FAILED+=("proot-distro command unavailable")
elif ! proot-distro login debian -- /bin/true >/dev/null 2>&1; then
  echo "  Debian distribution not found; installing it without touching other distributions..."
  if ! proot-distro install debian; then
    FAILED+=("install Debian proot distribution")
  fi
fi

if command -v proot-distro >/dev/null 2>&1 && proot-distro login debian -- /bin/true >/dev/null 2>&1; then
  echo
  echo "[6/6] Installing Debian proot packages, Python environment and Zsh stack..."
  PROOT_ARGS=(login debian --bind "$APP_ROOT:/mnt/termax-source" -- /usr/bin/env)
  if [[ "${TERMAX_DEBUG:-0}" == "1" ]]; then PROOT_ARGS+=(TERMAX_DEBUG=1); fi
  if [[ "${TERMAX_MINIMAL:-0}" == "1" ]]; then PROOT_ARGS+=(TERMAX_MINIMAL=1); fi
  PROOT_ARGS+=(/bin/bash --noprofile --norc /mnt/termax-source/termax/proot-bootstrap.sh install)
  proot-distro "${PROOT_ARGS[@]}" || FAILED+=("Debian proot bootstrap")
else
  FAILED+=("Debian proot unavailable; WW was left untouched")
fi


echo
echo "Final native Termux audit..."
FINAL_MISSING=()
for package in "${packages[@]}"; do
  if ! dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q "install ok installed"; then
    FINAL_MISSING+=("$package")
  fi
done
if (("${#FINAL_MISSING[@]}" > 0)); then
  printf '  Missing native packages: %s\n' "${FINAL_MISSING[*]}"
  FAILED+=("native Termux final package audit")
fi
if [[ "${TERMAX_MINIMAL:-0}" == "1" ]]; then
  modules=(rich)
else
  modules=(rich cloudscraper fastapi httplib2 opentelemetry requests requests_toolbelt uvicorn textual prompt_toolkit plotext networkx yaml typer)
fi
for module in "${modules[@]}"; do
  if ! python -c "import $module" >/dev/null 2>&1; then FAILED+=("native Python module: $module"); fi
done
if command -v zsh >/dev/null 2>&1; then
  [[ -d "$HOME/.oh-my-zsh" ]] || FAILED+=("native Oh My Zsh")
  [[ -f "$HOME/.zshrc" ]] || FAILED+=("native .zshrc")
  [[ -f "$HOME/.p10k.zsh" ]] || FAILED+=("native .p10k.zsh")
  [[ -f "$CUSTOM/themes/powerlevel10k/powerlevel10k.zsh-theme" ]] || FAILED+=("native Powerlevel10k")
  [[ -f "$CUSTOM/plugins/zsh-autosuggestions/zsh-autosuggestions.plugin.zsh" ]] || FAILED+=("native zsh-autosuggestions")
  [[ -f "$CUSTOM/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh" ]] || FAILED+=("native zsh-syntax-highlighting")
  [[ -f "$CUSTOM/plugins/zsh-autocomplete/zsh-autocomplete.plugin.zsh" ]] || FAILED+=("native zsh-autocomplete")
  [[ -f "$CUSTOM/plugins/zsh-history-substring-search/zsh-history-substring-search.zsh" ]] || FAILED+=("native zsh-history-substring-search")
  zsh -n "$HOME/.zshrc" || FAILED+=("native .zshrc syntax")
else
  FAILED+=("native zsh executable missing")
fi
echo
if (("${#FAILED[@]}" > 0)); then
  echo "TERMAX bootstrap completed with failures:"
  printf '  - %s\n' "${FAILED[@]}"
  echo "Review native log: $LOG"
  exit 1
fi
echo "TERMAX native Termux + Debian proot bootstrap complete."
echo "Zsh/Oh My Zsh/Powerlevel10k are installed in both environments."
echo "Existing .zshrc files were backed up before TERMAX changes."
echo "WW's repository, virtualenv and cookies were not modified."
echo "No login shell was changed automatically."
echo "Termux:API also requires the separate Android companion app and permissions."
