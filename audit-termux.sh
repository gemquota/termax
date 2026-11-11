#!/data/data/com.termux/files/usr/bin/bash
set -u
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PKG_FILE="$ROOT/config/termux-packages.txt"
PY_FILE="$ROOT/config/python-requirements.txt"
ok=0; missing=0
pass(){ printf '[OK]      %s\n' "$1"; ((ok+=1)); }
fail(){ printf '[MISSING] %s\n' "$1"; ((missing+=1)); }

echo "========== TERMAX ENVIRONMENT AUDIT =========="
echo "Termux: ${TERMUX_VERSION:-unknown} | $(uname -m)"
echo "Shell: $SHELL"
for c in zsh git python pip tmux curl wget jq fzf zoxide rg fd bat eza chafa dot gum nvim lazygit starship gh; do
  command -v "$c" >/dev/null 2>&1 && pass "$c" || fail "$c"
done
[[ -d "$HOME/.oh-my-zsh" ]] && pass "Oh My Zsh" || fail "Oh My Zsh"
[[ -f "$HOME/.zshrc" ]] && pass ".zshrc" || fail ".zshrc"
[[ -d "$HOME/.oh-my-zsh/custom/themes/powerlevel10k" ]] && pass "Powerlevel10k" || fail "Powerlevel10k"
for p in zsh-autosuggestions zsh-syntax-highlighting zsh-autocomplete zsh-history-substring-search; do
  [[ -f "$HOME/.oh-my-zsh/custom/plugins/$p/${p}.plugin.zsh" || -f "$HOME/.oh-my-zsh/custom/plugins/$p/$p.plugin.zsh" ]] && pass "$p" || fail "$p"
done
if command -v python >/dev/null 2>&1; then
  while read -r module; do
    [[ -z "$module" || "$module" == \#* ]] && continue
    case "$module" in
      PyYAML) import_name=yaml ;;
      prompt_toolkit) import_name=prompt_toolkit ;;
      opentelemetry-api) import_name=opentelemetry ;;
      *) import_name="$module" ;;
    esac
    python -c "import $import_name" >/dev/null 2>&1 && pass "Python: $module" || fail "Python: $module"
  done < "$PY_FILE"
fi
echo
echo "Summary: $ok passed; $missing missing."
echo "Package manifest is explicit top-level tooling, not every transitive Termux library."
echo "Termux:API requires the Android companion app and permissions."
exit $(( missing > 0 ? 1 : 0 ))
