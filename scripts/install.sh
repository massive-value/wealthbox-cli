#!/usr/bin/env bash
# wealthbox-cli bootstrap installer (macOS / Linux).
#
# One-line install:
#   curl -LsSf https://raw.githubusercontent.com/massive-value/wealthbox-cli/main/scripts/install.sh | bash
#
# Installs uv (if missing), installs wealthbox-cli as an isolated tool,
# prompts for the API token, and offers to install the AI agent skill.
set -euo pipefail

# When piped from curl, stdin is the pipe — redirect from the user's
# terminal so interactive prompts (token entry, skill picker) work.
if [ ! -t 0 ] && [ -e /dev/tty ]; then
    exec </dev/tty
fi

echo "=== wealthbox-cli installer ==="
echo

if ! command -v uv >/dev/null 2>&1; then
    echo "Installing uv (Python tool manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

if uv tool list 2>/dev/null | grep -qE '^wealthbox-cli[[:space:]]'; then
    echo "Upgrading wealthbox-cli to latest..."
    uv tool upgrade wealthbox-cli
else
    echo "Installing wealthbox-cli..."
    uv tool install wealthbox-cli
fi

# uv installs tool entry points to ~/.local/bin; ensure it's on PATH for
# the rest of this session.
export PATH="$HOME/.local/bin:$PATH"

if ! command -v wbox >/dev/null 2>&1; then
    echo
    echo "wbox installed but not on PATH in this shell."
    echo "Open a new terminal and run:"
    echo "    wbox config set-token"
    echo "    wbox skills install"
    exit 0
fi

echo
echo "Get your Wealthbox API token at https://dev.wealthbox.com"
echo "(Settings -> API Access -> Access Tokens)"
echo
wbox config set-token

echo
printf "Install the AI agent skill (Claude Code / Codex)? [Y/n] "
read -r install_skill || install_skill=""
case "$install_skill" in
    [Nn]*) echo "Skipped. Run 'wbox skills install' anytime." ;;
    *)     wbox skills install ;;
esac

echo
echo "Done. Try: wbox me"
