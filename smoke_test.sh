#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if [[ -z "${WEALTHBOX_TOKEN:-}" ]]; then
  echo "FAIL: WEALTHBOX_TOKEN is not set"
  exit 1
fi

echo "PASS: token loaded"

"$SCRIPT_DIR/.venv/bin/wbox" me --format json >/tmp/wealthbox-smoke-me.json
echo "PASS: wbox me"

"$SCRIPT_DIR/.venv/bin/wbox" users list --format json >/tmp/wealthbox-smoke-users.json
echo "PASS: wbox users list"

"$SCRIPT_DIR/.venv/bin/wbox" contacts list --per-page 1 --format json >/tmp/wealthbox-smoke-contacts.json
echo "PASS: wbox contacts list --per-page 1"

echo "SMOKE_TEST_OK"
