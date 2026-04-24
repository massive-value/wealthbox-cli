from __future__ import annotations

import httpx
import respx

from wealthbox_tools.cli.main import app


_BASE = "https://api.crmworkspace.com/v1"


@respx.mock
def test_doctor_reports_not_installed(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    respx.get(f"{_BASE}/me").mock(
        return_value=httpx.Response(200, json={"id": 1, "name": "x", "account": "y"})
    )
    result = runner.invoke(app, ["skills", "doctor"])
    assert result.exit_code == 0
    assert "not installed" in result.stdout.lower()
    assert "token ok" in result.stdout.lower()


@respx.mock
def test_doctor_reports_bad_token(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    respx.get(f"{_BASE}/me").mock(
        return_value=httpx.Response(401, json={"error": "unauthorized"})
    )
    result = runner.invoke(app, ["skills", "doctor"])
    assert "token" in result.stdout.lower()
    output = result.stdout.lower()
    assert "fail" in output or "unauthorized" in output or "invalid" in output


@respx.mock
def test_doctor_reports_installed_and_firm_name(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    dest = tmp_path / ".claude" / "skills" / "wealthbox-crm"
    dest.mkdir(parents=True)
    (dest / "SKILL.md").write_text("x")
    respx.get(f"{_BASE}/me").mock(
        return_value=httpx.Response(
            200, json={"id": 42, "name": "Kadin", "account": "Squire"}
        )
    )
    result = runner.invoke(app, ["skills", "doctor"])
    assert result.exit_code == 0
    assert "installed" in result.stdout.lower()
    assert "Kadin" in result.stdout or "Squire" in result.stdout
