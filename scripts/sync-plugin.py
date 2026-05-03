#!/usr/bin/env python3
"""Sync the canonical skill template to the plugin and codex marketplace copies.

Single source of truth: `src/wealthbox_tools/skills/wealthbox-crm/`.
Mirrors to:
  - `plugins/wealthbox-crm/skills/wealthbox-crm/`  (Claude Code plugin)
  - `codex-skill/wealthbox-crm/`                   (Codex skill submission)

Run before committing skill template changes:
    python scripts/sync-plugin.py

CI runs this then `git diff --exit-code` to fail if a developer forgot
to re-sync after editing the master copy.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE = REPO_ROOT / "src" / "wealthbox_tools" / "skills" / "wealthbox-crm"
TARGETS = [
    REPO_ROOT / "plugins" / "wealthbox-crm" / "skills" / "wealthbox-crm",
    REPO_ROOT / "codex-skill" / "wealthbox-crm",
]


def sync(source: Path, target: Path) -> None:
    if not source.is_dir():
        raise SystemExit(f"Source missing: {source}")
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)
    print(f"  {source} -> {target}")


def main() -> int:
    print(f"Syncing skill template from {SOURCE}:")
    for t in TARGETS:
        sync(SOURCE, t)
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
