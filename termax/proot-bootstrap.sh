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
CUSTOM="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"
VENV="$HOME/.local/share/termax/venv"

if [[ "$MODE" != "install" && "$MODE" != "check" && "$MODE" != "maintenance" ]]; then
  echo "Usage: proot-bootstrap.sh [install|check|maintenance]" >&2
  exit 2
fi
if [[ ! -f "$PACKAGE_FILE" || ! -f "$PYTHON_FILE" ]]; then
  echo "TERMAX Debian manifests are missing." >&2
  exit 2
fi
if [[ "${TERMAX_DEBUG:-0}" == "1" ]]; then set -x; fi
if [[ "$MODE" != "check" ]]; then exec > >(tee -a "$LOG") 2>&1; fi

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
if [[ "${TERMAX_MINIMAL:-0}" == "1" ]]; then
  minimal=(bash ca-certificates curl git python3 python3-pip python3-venv zsh fzf ripgrep fd-find jq)
  filtered=()
  for package in "${packages[@]}"; do
    for keep in "${minimal[@]}"; do
      if [[ "$package" == "$keep" ]]; then filtered+=("$package"); break; fi
    done
  done
  packages=("${filtered[@]}")
  echo "Minimal Debian package profile selected."
fi
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
FINAL_MISSING=()
for package in "${AVAILABLE[@]}"; do
  if ! dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q "install ok installed"; then
    FINAL_MISSING+=("$package")
  fi
done
ZSH_MISSING=()
[[ -d "$HOME/.oh-my-zsh" ]] || ZSH_MISSING+=("Oh My Zsh")
[[ -f "$HOME/.zshrc" ]] || ZSH_MISSING+=(".zshrc")
[[ -f "$HOME/.p10k.zsh" ]] || ZSH_MISSING+=(".p10k.zsh")
[[ -f "$CUSTOM/themes/powerlevel10k/powerlevel10k.zsh-theme" ]] || ZSH_MISSING+=("Powerlevel10k")
[[ -f "$CUSTOM/plugins/zsh-autosuggestions/zsh-autosuggestions.plugin.zsh" ]] || ZSH_MISSING+=("zsh-autosuggestions")
[[ -f "$CUSTOM/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh" ]] || ZSH_MISSING+=("zsh-syntax-highlighting")
[[ -f "$CUSTOM/plugins/zsh-autocomplete/zsh-autocomplete.plugin.zsh" ]] || ZSH_MISSING+=("zsh-autocomplete")
[[ -f "$CUSTOM/plugins/zsh-history-substring-search/zsh-history-substring-search.zsh" ]] || ZSH_MISSING+=("zsh-history-substring-search")
[[ -x "$VENV/bin/python" ]] || ZSH_MISSING+=("TERMAX Python venv")
if [[ -x "$VENV/bin/python" ]]; then
  if [[ "${TERMAX_MINIMAL:-0}" == "1" ]]; then modules=(rich); else modules=(rich cloudscraper fastapi httplib2 opentelemetry requests_toolbelt requests uvicorn textual prompt_toolkit plotext networkx yaml typer); fi
  for module in "${modules[@]}"; do
    "$VENV/bin/python" -c "import $module" >/dev/null 2>&1 || ZSH_MISSING+=("Python module: $module")
  done
fi
echo "Preflight Debian package audit: ${#FINAL_MISSING[@]} missing."
if (("${#FINAL_MISSING[@]}" > 0)); then printf '  still missing: %s\n' "${FINAL_MISSING[*]}"; fi
echo "Preflight Debian Zsh/Python audit: ${#ZSH_MISSING[@]} missing."
if (("${#ZSH_MISSING[@]}" > 0)); then printf '  still missing: %s\n' "${ZSH_MISSING[*]}"; fi

if (("${#UNAVAILABLE[@]}" > 0)); then printf '  not packaged here: %s\n' "${UNAVAILABLE[*]}"; fi

if [[ "$MODE" == "check" ]]; then
  echo "Python environment: $HOME/.local/share/termax/venv"
  echo "Zsh stack: Oh My Zsh, Powerlevel10k, autosuggestions, syntax-highlighting, autocomplete, history-substring-search"
  echo "READ-ONLY: no packages or files were changed."
  (("${#FINAL_MISSING[@]}" == 0 && "${#ZSH_MISSING[@]}" == 0 && "${#UNAVAILABLE[@]}" == 0)) || exit 1
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
  if [[ "${TERMAX_MINIMAL:-0}" == "1" ]]; then
    "$VENV/bin/python" -m pip install rich || FAILED+=("Debian minimal Python requirements")
  else
    "$VENV/bin/python" -m pip install -r "$PYTHON_FILE" || FAILED+=("Debian Python requirements")
  fi
  "$VENV/bin/python" -m pip check || FAILED+=("Debian Python dependency check")
fi

mkdir -p "$HOME/.local/bin"
if command -v fdfind >/dev/null 2>&1 && [[ ! -e "$HOME/.local/bin/fd" ]]; then ln -s "$(command -v fdfind)" "$HOME/.local/bin/fd"; fi
if command -v batcat >/dev/null 2>&1 && [[ ! -e "$HOME/.local/bin/bat" ]]; then ln -s "$(command -v batcat)" "$HOME/.local/bin/bat"; fi

CUSTOM="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"
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
    else
      echo "[FAILED] $dest exists but is not a Git checkout; preserving it."
      FAILED+=("unmanaged Zsh component: $dest")
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
managed_plugins = ["zsh-autosuggestions", "zsh-syntax-highlighting", "zsh-autocomplete", "zsh-history-substring-search", "colored-man-pages"]
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
fi


FINAL_MISSING=()
for package in "${AVAILABLE[@]}"; do
  if ! dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q "install ok installed"; then
    FINAL_MISSING+=("$package")
  fi
done
ZSH_MISSING=()
[[ -d "$HOME/.oh-my-zsh" ]] || ZSH_MISSING+=("Oh My Zsh")
[[ -f "$HOME/.zshrc" ]] || ZSH_MISSING+=(".zshrc")
[[ -f "$HOME/.p10k.zsh" ]] || ZSH_MISSING+=(".p10k.zsh")
[[ -f "$CUSTOM/themes/powerlevel10k/powerlevel10k.zsh-theme" ]] || ZSH_MISSING+=("Powerlevel10k")
[[ -f "$CUSTOM/plugins/zsh-autosuggestions/zsh-autosuggestions.plugin.zsh" ]] || ZSH_MISSING+=("zsh-autosuggestions")
[[ -f "$CUSTOM/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh" ]] || ZSH_MISSING+=("zsh-syntax-highlighting")
[[ -f "$CUSTOM/plugins/zsh-autocomplete/zsh-autocomplete.plugin.zsh" ]] || ZSH_MISSING+=("zsh-autocomplete")
[[ -f "$CUSTOM/plugins/zsh-history-substring-search/zsh-history-substring-search.zsh" ]] || ZSH_MISSING+=("zsh-history-substring-search")
[[ -x "$VENV/bin/python" ]] || ZSH_MISSING+=("TERMAX Python venv")
if [[ -x "$VENV/bin/python" ]]; then
  if [[ "${TERMAX_MINIMAL:-0}" == "1" ]]; then
    modules=(rich)
  else
    modules=(rich cloudscraper fastapi httplib2 opentelemetry requests_toolbelt requests uvicorn textual prompt_toolkit plotext networkx yaml typer)
  fi
  for module in "${modules[@]}"; do
    if ! "$VENV/bin/python" -c "import $module" >/dev/null 2>&1; then ZSH_MISSING+=("Python module: $module"); fi
  done
fi
if command -v zsh >/dev/null 2>&1 && [[ -f "$HOME/.zshrc" ]]; then
  zsh -n "$HOME/.zshrc" || ZSH_MISSING+=("Debian .zshrc syntax")
fi
echo "Final Debian package audit: ${#FINAL_MISSING[@]} missing."
if (("${#FINAL_MISSING[@]}" > 0)); then printf '  still missing: %s\n' "${FINAL_MISSING[*]}"; FAILED+=("Debian final package audit"); fi
echo "Final Debian Zsh/Python audit: ${#ZSH_MISSING[@]} missing."
if (("${#ZSH_MISSING[@]}" > 0)); then printf '  still missing: %s\n' "${ZSH_MISSING[*]}"; FAILED+=("Debian final Zsh/Python audit"); fi
if (("${#UNAVAILABLE[@]}" > 0)); then
  printf '  unavailable packages: %s\n' "${UNAVAILABLE[*]}"
  FAILED+=("Debian manifest contains unavailable packages")
fi
if (("${#FAILED[@]}" > 0)); then
  printf 'FAILED: %s\n' "${FAILED[*]}"
  exit 1
fi
echo "Debian proot environment bootstrap complete."
echo "WW's existing repository, virtualenv and cookies were not modified."
echo "No login shell was changed."
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
    backup = path.with_name(path.name + ".termax-backup-" + time.strftime("%Y%m%d-%H%M%S"))
    backup.write_text(original, encoding="utf-8")
    print(f"  Backed up previous Zsh config: {backup}")
    path.write_text(text, encoding="utf-8")
PY
  if [[ ! -f "$HOME/.p10k.zsh" && -f "$CUSTOM/themes/powerlevel10k/config/p10k-lean.zsh" ]]; then
    cp "$CUSTOM/themes/powerlevel10k/config/p10k-lean.zsh" "$HOME/.p10k.zsh"
  fi
fi


FINAL_MISSING=()
for package in "${AVAILABLE[@]}"; do
  if ! dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q "install ok installed"; then
    FINAL_MISSING+=("$package")
  fi
done
ZSH_MISSING=()
[[ -d "$HOME/.oh-my-zsh" ]] || ZSH_MISSING+=("Oh My Zsh")
[[ -f "$HOME/.zshrc" ]] || ZSH_MISSING+=(".zshrc")
[[ -f "$HOME/.p10k.zsh" ]] || ZSH_MISSING+=(".p10k.zsh")
[[ -f "$CUSTOM/themes/powerlevel10k/powerlevel10k.zsh-theme" ]] || ZSH_MISSING+=("Powerlevel10k")
[[ -f "$CUSTOM/plugins/zsh-autosuggestions/zsh-autosuggestions.plugin.zsh" ]] || ZSH_MISSING+=("zsh-autosuggestions")
[[ -f "$CUSTOM/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh" ]] || ZSH_MISSING+=("zsh-syntax-highlighting")
[[ -f "$CUSTOM/plugins/zsh-autocomplete/zsh-autocomplete.plugin.zsh" ]] || ZSH_MISSING+=("zsh-autocomplete")
[[ -f "$CUSTOM/plugins/zsh-history-substring-search/zsh-history-substring-search.zsh" ]] || ZSH_MISSING+=("zsh-history-substring-search")
[[ -x "$VENV/bin/python" ]] || ZSH_MISSING+=("TERMAX Python venv")
if [[ -x "$VENV/bin/python" ]]; then
  if [[ "${TERMAX_MINIMAL:-0}" == "1" ]]; then
    modules=(rich)
  else
    modules=(rich cloudscraper fastapi httplib2 opentelemetry requests_toolbelt requests uvicorn textual prompt_toolkit plotext networkx yaml typer)
  fi
  for module in "${modules[@]}"; do
    if ! "$VENV/bin/python" -c "import $module" >/dev/null 2>&1; then ZSH_MISSING+=("Python module: $module"); fi
  done
fi
if command -v zsh >/dev/null 2>&1 && [[ -f "$HOME/.zshrc" ]]; then
  zsh -n "$HOME/.zshrc" || ZSH_MISSING+=("Debian .zshrc syntax")
fi
echo "Final Debian package audit: ${#FINAL_MISSING[@]} missing."
if (("${#FINAL_MISSING[@]}" > 0)); then printf '  still missing: %s\n' "${FINAL_MISSING[*]}"; FAILED+=("Debian final package audit"); fi
echo "Final Debian Zsh/Python audit: ${#ZSH_MISSING[@]} missing."
if (("${#ZSH_MISSING[@]}" > 0)); then printf '  still missing: %s\n' "${ZSH_MISSING[*]}"; FAILED+=("Debian final Zsh/Python audit"); fi
if (("${#UNAVAILABLE[@]}" > 0)); then
  printf '  unavailable packages: %s\n' "${UNAVAILABLE[*]}"
  FAILED+=("Debian manifest contains unavailable packages")
fi
if (("${#FAILED[@]}" > 0)); then
  printf 'FAILED: %s\n' "${FAILED[*]}"
  exit 1
fi
echo "Debian proot environment bootstrap complete."
echo "WW's existing repository, virtualenv and cookies were not modified."
echo "No login shell was changed."
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
    backup = path.with_name(path.name + ".termax-backup-" + time.strftime("%Y%m%d-%H%M%S"))
    backup.write_text(original, encoding="utf-8")
    print(f"  Backed up previous Zsh config: {backup}")
    path.write_text(text, encoding="utf-8")
PY
  if [[ ! -f "$HOME/.p10k.zsh" && -f "$CUSTOM/themes/powerlevel10k/config/p10k-lean.zsh" ]]; then
    cp "$CUSTOM/themes/powerlevel10k/config/p10k-lean.zsh" "$HOME/.p10k.zsh"
  fi
fi


FINAL_MISSING=()
for package in "${AVAILABLE[@]}"; do
  if ! dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q "install ok installed"; then
    FINAL_MISSING+=("$package")
  fi
done
ZSH_MISSING=()
[[ -d "$HOME/.oh-my-zsh" ]] || ZSH_MISSING+=("Oh My Zsh")
[[ -f "$HOME/.zshrc" ]] || ZSH_MISSING+=(".zshrc")
[[ -f "$HOME/.p10k.zsh" ]] || ZSH_MISSING+=(".p10k.zsh")
[[ -f "$CUSTOM/themes/powerlevel10k/powerlevel10k.zsh-theme" ]] || ZSH_MISSING+=("Powerlevel10k")
[[ -f "$CUSTOM/plugins/zsh-autosuggestions/zsh-autosuggestions.plugin.zsh" ]] || ZSH_MISSING+=("zsh-autosuggestions")
[[ -f "$CUSTOM/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh" ]] || ZSH_MISSING+=("zsh-syntax-highlighting")
[[ -f "$CUSTOM/plugins/zsh-autocomplete/zsh-autocomplete.plugin.zsh" ]] || ZSH_MISSING+=("zsh-autocomplete")
[[ -f "$CUSTOM/plugins/zsh-history-substring-search/zsh-history-substring-search.zsh" ]] || ZSH_MISSING+=("zsh-history-substring-search")
[[ -x "$VENV/bin/python" ]] || ZSH_MISSING+=("TERMAX Python venv")
if [[ -x "$VENV/bin/python" ]]; then
  if [[ "${TERMAX_MINIMAL:-0}" == "1" ]]; then
    modules=(rich)
  else
    modules=(rich cloudscraper fastapi httplib2 opentelemetry requests_toolbelt requests uvicorn textual prompt_toolkit plotext networkx yaml typer)
  fi
  for module in "${modules[@]}"; do
    if ! "$VENV/bin/python" -c "import $module" >/dev/null 2>&1; then ZSH_MISSING+=("Python module: $module"); fi
  done
fi
if command -v zsh >/dev/null 2>&1 && [[ -f "$HOME/.zshrc" ]]; then
  zsh -n "$HOME/.zshrc" || ZSH_MISSING+=("Debian .zshrc syntax")
fi
echo "Final Debian package audit: ${#FINAL_MISSING[@]} missing."
if (("${#FINAL_MISSING[@]}" > 0)); then printf '  still missing: %s\n' "${FINAL_MISSING[*]}"; FAILED+=("Debian final package audit"); fi
echo "Final Debian Zsh/Python audit: ${#ZSH_MISSING[@]} missing."
if (("${#ZSH_MISSING[@]}" > 0)); then printf '  still missing: %s\n' "${ZSH_MISSING[*]}"; FAILED+=("Debian final Zsh/Python audit"); fi
if (("${#UNAVAILABLE[@]}" > 0)); then
  printf '  unavailable packages: %s\n' "${UNAVAILABLE[*]}"
  FAILED+=("Debian manifest contains unavailable packages")
fi
if (("${#FAILED[@]}" > 0)); then
  printf 'FAILED: %s\n' "${FAILED[*]}"
  exit 1
fi
echo "Debian proot environment bootstrap complete."
echo "WW's existing repository, virtualenv and cookies were not modified."
echo "No login shell was changed."
