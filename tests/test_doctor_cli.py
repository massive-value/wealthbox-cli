"""Tests for the top-level `wbox doctor` command.

`wbox skills doctor` is an alias of `wbox doctor` — both call run_doctor()
under the hood, so functional checks live in test_skills_cli_doctor.py.
This file pins the section ordering and the new fields surfaced by the
top-level command (CLI version, agent CLI detection, token source label,
summary line).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx
import respx

import wealthbox_tools.self_upgrade as su
from wealthbox_tools.cli.main import app

_BASE = "https://api.crmworkspace.com/v1"
_RELEASES_URL = (
    "https://api.github.com/repos/massive-value/wealthbox-cli/releases/latest"
)


def _release_payload(tag: str, published_at: str) -> dict:
    return {
        "tag_name": tag,
        "name": tag,
        "published_at": published_at,
        "assets": [],
    }


def _iso_z(dt: datetime) -> str:
    """Format a datetime as the RFC 3339 string GitHub returns ('...Z')."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _mock_me(name: str = "Adv", firm_id: int = 100, firm_name: str = "Firm") -> None:
    respx.get(f"{_BASE}/me").mock(
        return_value=httpx.Response(
            200, json={"id": 1, "name": name, "accounts": [{"id": firm_id, "name": firm_name}]}
        )
    )


@respx.mock
def test_doctor_top_level_command_exists(runner, tmp_path, monkeypatch):
    """`wbox doctor` (top-level) is registered and runs successfully."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    _mock_me()

    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0, result.stdout


@respx.mock
def test_doctor_includes_all_sections(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    _mock_me()

    result = runner.invoke(app, ["doctor"])
    out = result.stdout
    assert "# wbox CLI" in out
    assert "# Authentication" in out
    assert "# Agent CLIs on PATH" in out
    assert "# Skill installs" in out
    assert "# Firm data" in out
    assert "# Summary" in out


@respx.mock
def test_doctor_reports_cli_version_and_python(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    _mock_me()

    result = runner.invoke(app, ["doctor"])
    out = result.stdout
    assert "version:" in out
    assert "python:" in out


@respx.mock
def test_doctor_token_source_reports_env_var(runner, tmp_path, monkeypatch):
    """Token comes from WEALTHBOX_TOKEN (set by autouse mock_token fixture)."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    _mock_me()

    result = runner.invoke(app, ["doctor"])
    assert "env var" in result.stdout.lower() or "WEALTHBOX_TOKEN" in result.stdout


@respx.mock
def test_doctor_token_source_reports_flag(runner, tmp_path, monkeypatch):
    """When --token is passed, source should be reported as the flag."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    _mock_me()

    result = runner.invoke(app, ["doctor", "--token", "explicit-flag-token"])
    assert "--token flag" in result.stdout


@respx.mock
def test_doctor_summary_lists_issues_when_firm_not_bootstrapped(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    _mock_me()

    result = runner.invoke(app, ["doctor"])
    # No bootstrap has run -> firm-not-bootstrapped issue should appear.
    assert "issue(s) found" in result.stdout
    assert "firm data not bootstrapped" in result.stdout


@respx.mock
def test_doctor_summary_clean_when_everything_set(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    _mock_me()

    # Pre-seed canonical firm meta with onboarded_at so the doctor sees a
    # fully healthy state.
    from wealthbox_tools.cli._skill_paths import firm_meta_path
    firm_meta_path().parent.mkdir(parents=True, exist_ok=True)
    firm_meta_path().write_text(
        '{"identity": {"id": 1, "name": "Firm", "user_id": 1, "user_name": "Adv"}, '
        '"cli_version": "1.2.0", '
        '"files": {"categories.md": "2026-05-01T00:00:00+00:00"}, '
        '"onboarded_at": "2026-05-02T00:00:00+00:00"}'
    )

    result = runner.invoke(app, ["doctor"])
    assert "All checks passed" in result.stdout


@respx.mock
def test_skills_doctor_alias_calls_same_function(runner, tmp_path, monkeypatch):
    """`wbox skills doctor` and `wbox doctor` produce identical output."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    _mock_me()

    a = runner.invoke(app, ["doctor"])
    b = runner.invoke(app, ["skills", "doctor"])
    assert a.stdout == b.stdout


# ---------------------------------------------------------------------------
# 30-days-behind release warning (#41)
# ---------------------------------------------------------------------------


@respx.mock
def test_doctor_warns_when_behind_and_release_older_than_30_days(
    runner, tmp_path, monkeypatch
):
    """Behind + release >30 days old → doctor prints the upgrade nudge."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    _mock_me()

    # Pin running version older than the release tag.
    monkeypatch.setattr(su, "_running_version", lambda: "0.0.1")

    # Release published 45 days ago.
    published = datetime.now(timezone.utc) - timedelta(days=45)
    respx.get(_RELEASES_URL).mock(
        return_value=httpx.Response(
            200, json=_release_payload("v9.9.9", _iso_z(published))
        )
    )

    result = runner.invoke(app, ["doctor"])
    out = result.stdout
    assert "# Release age" in out
    # The warning text must surface the upgrade nudge.
    assert "9.9.9" in out
    assert "wbox self upgrade" in out
    # And it should be summarized as an issue.
    assert "issue(s) found" in out


@respx.mock
def test_doctor_no_warning_when_release_is_recent(runner, tmp_path, monkeypatch):
    """Behind but release <30 days old → no upgrade nudge fires."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    _mock_me()

    monkeypatch.setattr(su, "_running_version", lambda: "0.0.1")

    # Release published just 5 days ago.
    published = datetime.now(timezone.utc) - timedelta(days=5)
    respx.get(_RELEASES_URL).mock(
        return_value=httpx.Response(
            200, json=_release_payload("v9.9.9", _iso_z(published))
        )
    )

    result = runner.invoke(app, ["doctor"])
    out = result.stdout
    assert "# Release age" in out
    # Latest is rendered for transparency, but no upgrade nudge.
    assert "wbox self upgrade" not in out


@respx.mock
def test_doctor_no_warning_when_local_matches_latest(runner, tmp_path, monkeypatch):
    """Local version == latest release → no false positive even if old."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    _mock_me()

    monkeypatch.setattr(su, "_running_version", lambda: "1.2.3")

    # Release is 60 days old, but local matches → must not warn.
    published = datetime.now(timezone.utc) - timedelta(days=60)
    respx.get(_RELEASES_URL).mock(
        return_value=httpx.Response(
            200, json=_release_payload("v1.2.3", _iso_z(published))
        )
    )

    result = runner.invoke(app, ["doctor"])
    out = result.stdout
    assert "# Release age" in out
    assert "wbox self upgrade" not in out


@respx.mock
def test_doctor_soft_warning_on_network_error(runner, tmp_path, monkeypatch):
    """A network error during the release-age check is a soft warning, not a hard fail."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    _mock_me()

    respx.get(_RELEASES_URL).mock(side_effect=httpx.ConnectError("boom"))

    result = runner.invoke(app, ["doctor"])
    # Doctor still exits 0 (informational, not a gate).
    assert result.exit_code == 0
    out = result.stdout
    assert "# Release age" in out
    assert "could not check for updates" in out
    # The soft warning must NOT appear in the issues list.
    assert "wbox self upgrade" not in out
