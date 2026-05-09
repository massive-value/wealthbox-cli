#!/usr/bin/env bash
# wealthbox-cli bootstrap installer (macOS / Linux).
#
# One-line install:
#   curl -LsSf https://raw.githubusercontent.com/massive-value/wealthbox-cli/main/scripts/install.sh | bash
#
# Fetches a prebuilt ``wbox`` binary from the latest GitHub Release,
# verifies its SHA-256 against the release manifest, places it on PATH
# at ~/.local/bin/wbox, then prompts for the API token and offers to
# install the AI agent skill + bootstrap firm data.
#
# This script intentionally does NOT use pip / uv. It also never sudos
# and never chains to another curl-pipe-bash installer.
#
# The entire body lives inside main() so that bash reads the whole
# script into memory before executing. Without this, `curl | bash` reads
# the script as a stream from stdin — and any later stdin redirection
# (e.g. for /dev/tty prompts) would cut off bash's source mid-script and
# hang the install before it printed a single line.
#
# Step ordering (must match install.ps1):
#   1. detect-platform
#   2. resolve-release-via-github-api
#   3. download
#   4. verify-checksum
#   5. place-on-path
#   6. invoke `wbox skills install`
#   7. prompt-for-token
#   8. offer-firm-bootstrap

set -euo pipefail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO="massive-value/wealthbox-cli"
RELEASES_LATEST_API="https://api.github.com/repos/${REPO}/releases/latest"
MANIFEST_NAME="SHA256SUMS.txt"
INSTALL_DIR="${HOME}/.local/bin"
BINARY_NAME="wbox"
PATH_SENTINEL="# added by wealthbox-cli installer"

# Mutated by --dry-run.
DRY_RUN=0

# Populated by the steps below; downstream steps consume them.
PLATFORM_TAG=""
ASSET_NAME=""
RELEASE_TAG=""
RELEASE_JSON=""
BINARY_URL=""
MANIFEST_URL=""
EXPECTED_SHA256=""
DOWNLOAD_DIR=""
DOWNLOADED_BINARY=""
TTY_SOURCE=""

# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

log() { printf '%s\n' "$*"; }
step() { printf '\n[*] %s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }
err() { printf 'error: %s\n' "$*" >&2; }

dry_log() {
    if [ "$DRY_RUN" -eq 1 ]; then
        printf '[dry-run] %s\n' "$*"
    fi
}

# ---------------------------------------------------------------------------
# Tool detection — the script needs curl + a sha256 utility. uname is in
# coreutils on Linux and base on macOS, so we don't probe for it.
# ---------------------------------------------------------------------------

require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        err "required command not found: $1"
        exit 1
    fi
}

sha256_of() {
    local file="$1"
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$file" | awk '{print $1}'
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$file" | awk '{print $1}'
    else
        err "no sha256 utility found (need sha256sum or shasum)"
        exit 1
    fi
}

# ---------------------------------------------------------------------------
# 1. detect-platform
# ---------------------------------------------------------------------------

detect_platform() {
    step "Detecting platform..."

    local kernel arch
    kernel="$(uname -s)"
    arch="$(uname -m)"

    case "$kernel" in
        Darwin)
            case "$arch" in
                arm64|aarch64)
                    PLATFORM_TAG="macos-arm64"
                    ASSET_NAME="wbox-macos-arm64"
                    ;;
                x86_64|amd64)
                    PLATFORM_TAG="macos-x64"
                    ASSET_NAME="wbox-macos-x64"
                    ;;
                *)
                    err "unsupported macOS architecture: ${arch}"
                    err "supported: arm64, x86_64"
                    exit 1
                    ;;
            esac
            ;;
        Linux)
            case "$arch" in
                x86_64|amd64)
                    PLATFORM_TAG="linux-x64"
                    ASSET_NAME="wbox-linux-x64"
                    ;;
                *)
                    err "unsupported Linux architecture: ${arch}"
                    err "supported: x86_64"
                    err "(Linux arm64 is not yet built — see https://github.com/${REPO}/releases)"
                    exit 1
                    ;;
            esac
            ;;
        *)
            err "unsupported operating system: ${kernel}"
            err "supported: macOS (Darwin), Linux"
            exit 1
            ;;
    esac

    log "  platform: ${PLATFORM_TAG}"
    log "  asset:    ${ASSET_NAME}"
}

# ---------------------------------------------------------------------------
# 2. resolve-release-via-github-api
# ---------------------------------------------------------------------------
#
# Anonymous request to /repos/.../releases/latest. On 403 (rate limit) we
# print a clear message and exit non-zero — never silently fall back.
# Even with --dry-run, this read-only network call still happens (the
# acceptance criteria allows the GitHub API GET in dry-run mode).

resolve_release() {
    step "Querying GitHub for the latest release..."

    require_cmd curl

    local http_code
    local body_file
    # Portable mktemp invocation: GNU and BSD both accept an explicit
    # template path with at least 6 trailing X's. The -t flag's behavior
    # diverges between the two, so we avoid it.
    body_file="$(mktemp "${TMPDIR:-/tmp}/wbox-release.XXXXXX")"

    # -w writes the HTTP code; -o captures the body. We tolerate non-200
    # so we can produce a clear error.
    http_code="$(
        curl -sS -L \
            -H 'Accept: application/vnd.github+json' \
            -H 'X-GitHub-Api-Version: 2022-11-28' \
            -o "$body_file" \
            -w '%{http_code}' \
            "$RELEASES_LATEST_API" \
        || true
    )"

    case "$http_code" in
        200)
            ;;
        403)
            err "GitHub API returned 403 (rate-limited or forbidden)."
            err "  Wait for the per-IP limit to reset (typically 1 hour) or set GITHUB_TOKEN."
            err "  Manual install: https://github.com/${REPO}/releases/latest"
            rm -f "$body_file"
            exit 1
            ;;
        404)
            err "GitHub API returned 404. Repository or releases not found:"
            err "  ${RELEASES_LATEST_API}"
            rm -f "$body_file"
            exit 1
            ;;
        *)
            err "GitHub API request failed with HTTP ${http_code}."
            err "  ${RELEASES_LATEST_API}"
            rm -f "$body_file"
            exit 1
            ;;
    esac

    RELEASE_JSON="$(cat "$body_file")"
    rm -f "$body_file"

    # Parse without depending on jq. Fields we need:
    #   tag_name           -> RELEASE_TAG
    #   assets[].name + browser_download_url for $ASSET_NAME and SHA256SUMS.txt
    RELEASE_TAG="$(
        printf '%s' "$RELEASE_JSON" \
        | grep -E '"tag_name"[[:space:]]*:' \
        | head -n1 \
        | sed -E 's/.*"tag_name"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/'
    )"
    if [ -z "$RELEASE_TAG" ]; then
        err "could not parse tag_name from GitHub API response."
        exit 1
    fi

    BINARY_URL="$(extract_asset_url "$ASSET_NAME")"
    if [ -z "$BINARY_URL" ]; then
        err "no asset named '${ASSET_NAME}' found on release ${RELEASE_TAG}."
        err "  Visit https://github.com/${REPO}/releases/tag/${RELEASE_TAG} for the asset list."
        exit 1
    fi

    MANIFEST_URL="$(extract_asset_url "$MANIFEST_NAME")"
    if [ -z "$MANIFEST_URL" ]; then
        err "no '${MANIFEST_NAME}' asset on release ${RELEASE_TAG}."
        err "  This installer requires a checksum manifest; refusing to continue."
        exit 1
    fi

    log "  release:  ${RELEASE_TAG}"
    log "  binary:   ${BINARY_URL}"
    log "  manifest: ${MANIFEST_URL}"
}

# Pull a browser_download_url out of the assets array by matching the
# adjacent "name" field. Avoids jq so the script runs on a stock macOS /
# Debian box. Walks the JSON one asset object at a time.
extract_asset_url() {
    local target="$1"
    # First normalise whitespace, then split *only* at top-level array
    # boundaries (`},{`) — NOT on every `{`. The earlier `s/{/\n{/g`
    # version broke on real release payloads because each asset has a
    # nested `uploader` object: that object's opening `{` would split
    # the asset, leaving "name" on one line and "browser_download_url"
    # on another, and the grep+sed pipeline returned nothing.
    printf '%s' "$RELEASE_JSON" \
        | tr -d '\n' \
        | sed -E 's/[[:space:]]+//g' \
        | sed 's/},{/}\n{/g' \
        | grep -F "\"name\":\"${target}\"" \
        | head -n1 \
        | sed -E 's/.*"browser_download_url":"([^"]+)".*/\1/'
}

# ---------------------------------------------------------------------------
# 3. download
# 4. verify-checksum
# ---------------------------------------------------------------------------
#
# Idempotence: if ~/.local/bin/wbox already exists AND its sha256 matches
# the manifest entry for our asset, we skip the network download entirely
# and just continue to subsequent steps. This makes re-runs cheap.

read_expected_sha256() {
    # Fetch the manifest, extract the line for our binary, take the first
    # whitespace token (the hex digest).
    local manifest
    manifest="$(curl -sSfL "$MANIFEST_URL")" || {
        err "failed to download ${MANIFEST_NAME} from ${MANIFEST_URL}"
        exit 1
    }
    EXPECTED_SHA256="$(
        printf '%s\n' "$manifest" \
        | awk -v name="$ASSET_NAME" '$2 == name { print $1; exit }'
    )"
    if [ -z "$EXPECTED_SHA256" ]; then
        err "no entry for ${ASSET_NAME} in ${MANIFEST_NAME}."
        err "manifest contents:"
        printf '%s\n' "$manifest" >&2
        exit 1
    fi
}

download_binary() {
    step "Downloading ${ASSET_NAME} (${RELEASE_TAG})..."

    read_expected_sha256
    log "  expected sha256: ${EXPECTED_SHA256}"

    local installed_path="${INSTALL_DIR}/${BINARY_NAME}"
    if [ -f "$installed_path" ]; then
        local installed_sha
        installed_sha="$(sha256_of "$installed_path")"
        if [ "$installed_sha" = "$EXPECTED_SHA256" ]; then
            log "  ${BINARY_NAME} already at this version (sha256 matches) — skipping download."
            DOWNLOADED_BINARY=""  # signal to place_on_path that nothing to install
            return 0
        fi
        log "  existing ${BINARY_NAME} differs — will upgrade."
    fi

    if [ "$DRY_RUN" -eq 1 ]; then
        dry_log "would download ${BINARY_URL}"
        dry_log "would verify sha256 against ${EXPECTED_SHA256}"
        DOWNLOADED_BINARY=""
        return 0
    fi

    DOWNLOAD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/wbox-install.XXXXXX")"
    DOWNLOADED_BINARY="${DOWNLOAD_DIR}/${BINARY_NAME}"

    curl -sSfL -o "$DOWNLOADED_BINARY" "$BINARY_URL" || {
        err "failed to download ${BINARY_URL}"
        rm -rf "$DOWNLOAD_DIR"
        exit 1
    }

    verify_checksum
}

verify_checksum() {
    step "Verifying SHA-256..."

    local actual
    actual="$(sha256_of "$DOWNLOADED_BINARY")"

    if [ "$actual" != "$EXPECTED_SHA256" ]; then
        err "checksum mismatch for ${ASSET_NAME}"
        err "  expected: ${EXPECTED_SHA256}"
        err "  actual:   ${actual}"
        rm -rf "$DOWNLOAD_DIR"
        exit 1
    fi

    log "  OK (${actual})"
}

# ---------------------------------------------------------------------------
# 5. place-on-path
# ---------------------------------------------------------------------------
#
# Install at ~/.local/bin/wbox. If $HOME/.local/bin is not on PATH, append
# the export to the user's shell rc with a unique sentinel comment so
# re-runs do not duplicate the line.

place_on_path() {
    step "Installing to ${INSTALL_DIR}/${BINARY_NAME}..."

    if [ -z "$DOWNLOADED_BINARY" ]; then
        log "  (no new binary to place — already up to date)"
    else
        if [ "$DRY_RUN" -eq 1 ]; then
            dry_log "would mkdir -p ${INSTALL_DIR}"
            dry_log "would install ${DOWNLOADED_BINARY} -> ${INSTALL_DIR}/${BINARY_NAME}"
        else
            mkdir -p "$INSTALL_DIR"
            chmod +x "$DOWNLOADED_BINARY"
            # mv is atomic within the same filesystem; the tmpdir lives under
            # $TMPDIR which on macOS/Linux is the same volume as $HOME for
            # the typical user. Falls through to copy on cross-device edge cases.
            mv -f "$DOWNLOADED_BINARY" "${INSTALL_DIR}/${BINARY_NAME}"
            rm -rf "$DOWNLOAD_DIR"
        fi
    fi

    ensure_path_persisted
}

ensure_path_persisted() {
    # If the user's *interactive* PATH already includes $INSTALL_DIR, we
    # don't need to mutate any rc. We can't check the interactive PATH
    # from a curl-pipe-bash session reliably, so we also peek into the
    # rc files to see if a previous installer run already added the line.
    local rc
    rc="$(detect_shell_rc)"

    if [ -z "$rc" ]; then
        warn "could not determine which shell rc to update."
        warn "manually add this to your shell startup file:"
        warn "  export PATH=\"\$HOME/.local/bin:\$PATH\""
        return 0
    fi

    # Already added by a previous install? Match the sentinel exactly.
    if [ -f "$rc" ] && grep -Fq "$PATH_SENTINEL" "$rc"; then
        log "  PATH already configured in ${rc} (sentinel found) — skipping."
        return 0
    fi

    # Already on the active PATH? Then there's nothing to do — but still
    # record an idempotent sentinel block so future shells inherit it.
    case ":${PATH}:" in
        *":${INSTALL_DIR}:"*)
            log "  ${INSTALL_DIR} already on PATH for this shell."
            # Continue to write the sentinel so this is durable.
            ;;
    esac

    if [ "$DRY_RUN" -eq 1 ]; then
        dry_log "would append PATH export to ${rc} with sentinel '${PATH_SENTINEL}'"
        return 0
    fi

    # Make sure the rc directory exists (e.g. ~/.config/fish/) before append.
    mkdir -p "$(dirname "$rc")"

    case "$rc" in
        */config.fish)
            {
                printf '\n%s\n' "$PATH_SENTINEL"
                printf 'set -gx PATH $HOME/.local/bin $PATH\n'
            } >> "$rc"
            ;;
        *)
            {
                printf '\n%s\n' "$PATH_SENTINEL"
                printf 'export PATH="$HOME/.local/bin:$PATH"\n'
            } >> "$rc"
            ;;
    esac
    log "  PATH updated in ${rc}."
    log "  Open a new terminal (or 'source ${rc}') to pick up the change."

    # Make subsequent steps in *this* script run see the new PATH.
    export PATH="${INSTALL_DIR}:${PATH}"
}

detect_shell_rc() {
    # Prefer $SHELL (set by login); fall back to inspecting which rc file
    # actually exists. On macOS the default is zsh; on most Linux distros
    # it's bash.
    local shell_name="${SHELL:-}"
    case "$(basename "${shell_name:-bash}")" in
        zsh)
            printf '%s\n' "${ZDOTDIR:-$HOME}/.zshrc"
            ;;
        bash)
            # Linux conventionally uses ~/.bashrc; macOS often uses
            # ~/.bash_profile. Prefer whichever exists, falling back to
            # ~/.bashrc as the canonical interactive-rc.
            if [ -f "$HOME/.bashrc" ]; then
                printf '%s\n' "$HOME/.bashrc"
            elif [ -f "$HOME/.bash_profile" ]; then
                printf '%s\n' "$HOME/.bash_profile"
            else
                printf '%s\n' "$HOME/.bashrc"
            fi
            ;;
        fish)
            printf '%s\n' "${HOME}/.config/fish/config.fish"
            ;;
        *)
            # Unknown shell: most Bourne-family shells respect ~/.profile.
            printf '%s\n' "$HOME/.profile"
            ;;
    esac
}

# ---------------------------------------------------------------------------
# TTY discovery — used by every interactive prompt below.
# ---------------------------------------------------------------------------
#
# When piped from curl, stdin is the pipe (not a tty) but /dev/tty is
# usually still attached to the user's terminal. If neither is true, we
# skip prompts and tell the user how to finish manually.

discover_tty() {
    if [ -t 0 ]; then
        TTY_SOURCE="stdin"
    elif [ -r /dev/tty ] && [ -w /dev/tty ] && (: < /dev/tty) >/dev/null 2>&1; then
        TTY_SOURCE="/dev/tty"
    else
        TTY_SOURCE=""
    fi
}

# Read a line from whichever tty source we discovered. Echoes nothing on
# its own — caller is responsible for the prompt. Result is in $REPLY
# (the implicit default for `read`).
read_tty() {
    REPLY=""
    if [ "$TTY_SOURCE" = "/dev/tty" ]; then
        IFS= read -r REPLY </dev/tty || REPLY=""
    elif [ "$TTY_SOURCE" = "stdin" ]; then
        IFS= read -r REPLY || REPLY=""
    fi
}

# ---------------------------------------------------------------------------
# 6. invoke `wbox skills install`
# ---------------------------------------------------------------------------

invoke_skills_install() {
    step "Installing the wealthbox-crm AI agent skill..."

    if [ "$DRY_RUN" -eq 1 ]; then
        dry_log "would run: wbox skills install --no-bootstrap"
        return 0
    fi

    if ! command -v wbox >/dev/null 2>&1; then
        warn "'wbox' is not yet on PATH in this shell."
        warn "open a new terminal and run:"
        warn "  wbox skills install"
        warn "  wbox config set-token"
        return 0
    fi

    # We pass --no-bootstrap so the script controls the bootstrap prompt
    # in step 8 (the issue spec says the firm-bootstrap prompt is a
    # separate, named step). The skill installer itself will detect hosts
    # interactively if no --platform is supplied.
    if [ "$TTY_SOURCE" = "/dev/tty" ]; then
        wbox skills install --no-bootstrap </dev/tty || warn "'wbox skills install' returned non-zero."
    elif [ "$TTY_SOURCE" = "stdin" ]; then
        wbox skills install --no-bootstrap || warn "'wbox skills install' returned non-zero."
    else
        # No tty: pick a sensible default platform without prompting.
        wbox skills install --platform claude-code-user --no-bootstrap \
            || warn "'wbox skills install --platform claude-code-user' returned non-zero."
    fi
}

# ---------------------------------------------------------------------------
# 7. prompt-for-token
# ---------------------------------------------------------------------------

prompt_for_token() {
    step "Saving the Wealthbox API token..."

    if [ "$DRY_RUN" -eq 1 ]; then
        dry_log "would run: wbox config set-token"
        return 0
    fi

    if ! command -v wbox >/dev/null 2>&1; then
        warn "'wbox' not on PATH; skipping token prompt."
        warn "run later: wbox config set-token"
        return 0
    fi

    if [ -z "$TTY_SOURCE" ]; then
        log "  No interactive terminal detected. Run later:"
        log "    wbox config set-token"
        return 0
    fi

    log "  Get your token at https://dev.wealthbox.com"
    log "  (Settings -> API Access -> Access Tokens)"
    if [ "$TTY_SOURCE" = "/dev/tty" ]; then
        wbox config set-token </dev/tty || warn "'wbox config set-token' returned non-zero."
    else
        wbox config set-token || warn "'wbox config set-token' returned non-zero."
    fi
}

# ---------------------------------------------------------------------------
# 8. offer-firm-bootstrap
# ---------------------------------------------------------------------------

offer_firm_bootstrap() {
    step "Bootstrap firm data?"

    if [ "$DRY_RUN" -eq 1 ]; then
        dry_log "would prompt: 'Run wbox skills bootstrap now? [Y/n]'"
        return 0
    fi

    if ! command -v wbox >/dev/null 2>&1; then
        return 0
    fi

    if [ -z "$TTY_SOURCE" ]; then
        log "  Skipped (no interactive terminal). Run later:"
        log "    wbox skills bootstrap"
        return 0
    fi

    printf "Run 'wbox skills bootstrap' to populate firm data now? [Y/n] "
    read_tty
    case "${REPLY:-}" in
        [Nn]*)
            log "  Skipped. Run anytime: wbox skills bootstrap"
            ;;
        *)
            if [ "$TTY_SOURCE" = "/dev/tty" ]; then
                wbox skills bootstrap </dev/tty || warn "'wbox skills bootstrap' returned non-zero."
            else
                wbox skills bootstrap || warn "'wbox skills bootstrap' returned non-zero."
            fi
            ;;
    esac
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

parse_args() {
    while [ $# -gt 0 ]; do
        case "$1" in
            --dry-run)
                DRY_RUN=1
                shift
                ;;
            -h|--help)
                cat <<'USAGE'
wealthbox-cli installer (macOS / Linux)

Usage:
  install.sh [--dry-run] [--help]

Options:
  --dry-run   Print the steps the installer would take without making
              filesystem changes. The GitHub API GET still happens so
              the dry-run can show the resolved release tag.
  -h, --help  Show this message and exit.
USAGE
                exit 0
                ;;
            *)
                err "unknown argument: $1"
                err "try '--help'"
                exit 2
                ;;
        esac
    done
}

# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

main() {
    parse_args "$@"

    log "=== wealthbox-cli installer ==="
    if [ "$DRY_RUN" -eq 1 ]; then
        log "(dry-run mode — no filesystem changes will be made)"
    fi

    discover_tty

    detect_platform                 # 1
    resolve_release                 # 2
    download_binary                 # 3 + 4 (download + verify-checksum)
    place_on_path                   # 5
    invoke_skills_install           # 6
    prompt_for_token                # 7
    offer_firm_bootstrap            # 8

    log ""
    log "Done."
    if ! command -v wbox >/dev/null 2>&1; then
        log "If 'wbox' is not yet on PATH, open a new terminal and try: wbox me"
    else
        log "Try: wbox me"
    fi
}

main "$@"
