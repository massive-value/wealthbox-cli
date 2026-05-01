from __future__ import annotations

import json

from wealthbox_tools.cli.main import app


def _seed_install_with_firm(tmp_path, *, with_onboarded: bool = False):
    """Set up a claude-code-user install with a populated firm section."""
    dest = tmp_path / ".claude" / "skills" / "wealthbox-crm"
    dest.mkdir(parents=True)
    (dest / "SKILL.md").write_text("x")
    firm: dict[str, object] = {
        "identity": {"id": 2, "name": "y", "user_id": 1, "user_name": "x"},
        "cli_version": "1.1.6",
        "files": {"categories.md": "2026-01-01T00:00:00+00:00"},
    }
    if with_onboarded:
        firm["onboarded_at"] = "2026-04-15T12:00:00+00:00"
    (dest / "_meta.json").write_text(json.dumps({"firm": firm}))
    return dest


def test_mark_onboarded_stamps_meta(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    dest = _seed_install_with_firm(tmp_path)

    result = runner.invoke(app, ["skills", "mark-onboarded"])
    assert result.exit_code == 0, (result.stdout, result.stderr)

    meta = json.loads((dest / "_meta.json").read_text())
    onboarded = meta["firm"].get("onboarded_at")
    assert onboarded is not None
    assert onboarded.startswith("20")  # ISO 8601 timestamp


def test_mark_onboarded_fails_without_firm_section(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    dest = tmp_path / ".claude" / "skills" / "wealthbox-crm"
    dest.mkdir(parents=True)
    (dest / "SKILL.md").write_text("x")
    # No _meta.json yet — bootstrap hasn't run.

    result = runner.invoke(app, ["skills", "mark-onboarded"])
    assert result.exit_code != 0
    output = (result.stdout or "") + (result.stderr or "")
    assert "bootstrap" in output.lower()


def test_mark_onboarded_errors_when_nothing_installed(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["skills", "mark-onboarded"])
    assert result.exit_code != 0
    output = (result.stdout or "") + (result.stderr or "")
    assert "no installed" in output.lower()
