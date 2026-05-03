#!/usr/bin/env bash
# wealthbox-cli bootstrap installer (macOS / Linux).
#
# One-line install:
#   curl -LsSf https://raw.githubusercontent.com/massive-value/wealthbox-cli/main/scripts/install.sh | bash
#
# Installs uv (if missing), installs wealthbox-cli as an isolated tool,
# prompts for the API token, and offers to install the AI agent skill.
#
# Note: the entire body lives inside main() so that bash reads the whole
# script into memory before executing. Without this, `curl | bash` reads
# the script as a stream from stdin — and any later stdin redirection
# (e.g. for /dev/tty prompts) would cut off bash's source mid-script and
# hang the install before it printed a single line.
set -euo pipefail

main() {
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

    # uv installs tool entry points to ~/.local/bin; ensure it's on PATH
    # for the rest of this session.
    export PATH="$HOME/.local/bin:$PATH"

    if ! command -v wbox >/dev/null 2>&1; then
        echo
        echo "wbox installed but not on PATH in this shell."
        echo "Open a new terminal and run:"
        echo "    wbox config set-token"
        echo "    wbox skills install"
        return 0
    fi

    # Detect whether we have a real terminal for the interactive prompts.
    # When piped from curl, stdin is the pipe (not a tty) but /dev/tty is
    # usually still attached to the user's terminal. If neither is true,
    # skip the prompts and tell the user how to finish manually.
    local tty=""
    if [ -t 0 ]; then
        tty="stdin"
    elif [ -r /dev/tty ] && [ -w /dev/tty ] && (: < /dev/tty) >/dev/null 2>&1; then
        tty="/dev/tty"
    fi

    if [ -z "$tty" ]; then
        echo
        echo "wbox is installed. To finish setup, run from an interactive shell:"
        echo "    wbox config set-token"
        echo "    wbox skills install"
        return 0
    fi

    echo
    echo "Get your Wealthbox API token at https://dev.wealthbox.com"
    echo "(Settings -> API Access -> Access Tokens)"
    echo
    if [ "$tty" = "/dev/tty" ]; then
        wbox config set-token </dev/tty
    else
        wbox config set-token
    fi

    echo
    if [ "$tty" = "/dev/tty" ]; then
        printf "Install the AI agent skill (Claude Code / Codex)? [Y/n] "
        read -r install_skill </dev/tty || install_skill=""
    else
        printf "Install the AI agent skill (Claude Code / Codex)? [Y/n] "
        read -r install_skill || install_skill=""
    fi

    case "$install_skill" in
        [Nn]*) echo "Skipped. Run 'wbox skills install' anytime." ;;
        *)
            if [ "$tty" = "/dev/tty" ]; then
                wbox skills install </dev/tty
            else
                wbox skills install
            fi
            ;;
    esac

    echo
    echo "Done. Try: wbox me"
}

main "$@"
