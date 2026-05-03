from __future__ import annotations

import json

from wealthbox_tools.cli._skill_paths import firm_meta_path
from wealthbox_tools.cli.main import app


def _seed_canonical_firm_meta(*, with_onboarded: bool = False):
    """Seed the canonical firm meta as if `wbox skills bootstrap` had run."""
    meta: dict[str, object] = {
        "identity": {"id": 2, "name": "y", "user_id": 1, "user_name": "x"},
        "cli_version": "1.1.6",
        "files": {"categories.md": "2026-01-01T00:00:00+00:00"},
    }
    if with_onboarded:
        meta["onboarded_at"] = "2026-04-15T12:00:00+00:00"
    firm_meta_path().parent.mkdir(parents=True, exist_ok=True)
    firm_meta_path().write_text(json.dumps(meta))


def test_mark_onboarded_stamps_canonical_meta(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    _seed_canonical_firm_meta()

    result = runner.invoke(app, ["skills", "mark-onboarded"])
    assert result.exit_code == 0, (result.stdout, result.stderr)

    meta = json.loads(firm_meta_path().read_text())
    onboarded = meta.get("onboarded_at")
    assert onboarded is not None
    assert onboarded.startswith("20")  # ISO 8601 timestamp


def test_mark_onboarded_fails_without_firm_meta(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    # No firm meta yet — bootstrap hasn't run.

    result = runner.invoke(app, ["skills", "mark-onboarded"])
    assert result.exit_code != 0
    output = (result.stdout or "") + (result.stderr or "")
    assert "bootstrap" in output.lower()
