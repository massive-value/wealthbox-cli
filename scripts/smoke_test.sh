#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

if [[ -z "${WEALTHBOX_TOKEN:-}" ]]; then
  echo "FAIL: WEALTHBOX_TOKEN is not set"
  exit 1
fi

echo "PASS: token loaded"

uv run wbox me --format json >/tmp/wealthbox-smoke-me.json
echo "PASS: wbox me"

uv run wbox users list --format json >/tmp/wealthbox-smoke-users.json
echo "PASS: wbox users list"

uv run wbox contacts list --per-page 1 --format json >/tmp/wealthbox-smoke-contacts.json
echo "PASS: wbox contacts list --per-page 1"

echo "SMOKE_TEST_OK"
