"""Canonical machine-level paths for skill firm data.

Firm data (generated category/custom-field/user files, hand-edited policy,
firm identity, onboarded marker) lives at one canonical location per machine,
not inside each skill install. This survives plugin auto-updates and skill
template upgrades that would otherwise wipe firm state.

Per-install metadata (template `cli_version`) still lives in
`<skill_dir>/_meta.json` because each platform may run a different template
version.
"""
from __future__ import annotations

from pathlib import Path

from ._config import _config_dir


def firm_dir() -> Path:
    """Return the canonical firm data directory.

    Mac/Linux: `~/.config/wbox/firm/`
    Windows:   `%APPDATA%\\wbox\\firm\\`
    """
    return _config_dir() / "firm"


def firm_meta_path() -> Path:
    """Return the canonical firm metadata JSON path.

    Stores `identity`, `cli_version`, generated-file timestamps, and
    `onboarded_at` — the same shape as the old `_meta.json.firm` section.
    """
    return firm_dir() / "_meta.json"
