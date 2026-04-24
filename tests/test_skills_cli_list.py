from __future__ import annotations

from wealthbox_tools.cli.main import app


def test_skills_list_reports_not_installed_for_fresh_env(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["skills", "list"])
    assert result.exit_code == 0
    assert "claude-code-user" in result.stdout
    assert "codex" in result.stdout
    assert "not installed" in result.stdout.lower()


def test_skills_list_reports_installed_after_copy(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    target = tmp_path / ".claude" / "skills" / "wealthbox-crm"
    target.mkdir(parents=True)
    (target / "SKILL.md").write_text("x")
    result = runner.invoke(app, ["skills", "list"])
    assert result.exit_code == 0
    assert "installed" in result.stdout.lower()
