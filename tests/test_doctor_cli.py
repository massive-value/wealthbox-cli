"""Tests for the top-level `wbox doctor` command.

`wbox skills doctor` is an alias of `wbox doctor` — both call run_doctor()
under the hood, so functional checks live in test_skills_cli_doctor.py.
This file pins the section ordering and the new fields surfaced by the
top-level command (CLI version, agent CLI detection, token source label,
summary line).
"""
from __future__ import annotations

import httpx
import respx

from wealthbox_tools.cli.main import app

_BASE = "https://api.crmworkspace.com/v1"


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
    assert "# Plugin installs" in out
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
