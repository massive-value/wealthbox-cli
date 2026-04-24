from __future__ import annotations

from wealthbox_tools.cli.main import app


def test_uninstall_removes_skill_dir(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    runner.invoke(
        app, ["skills", "install", "--platform", "claude-code-user", "--no-bootstrap"]
    )
    dest = tmp_path / ".claude" / "skills" / "wealthbox-crm"
    assert dest.exists()
    result = runner.invoke(
        app, ["skills", "uninstall", "--platform", "claude-code-user", "--yes"]
    )
    assert result.exit_code == 0, result.stdout
    assert not dest.exists()
    assert (tmp_path / ".claude" / "skills").exists()


def test_uninstall_noop_when_not_installed(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app, ["skills", "uninstall", "--platform", "claude-code-user", "--yes"]
    )
    assert result.exit_code == 0, result.stdout
    output = result.stdout.lower()
    assert "not installed" in output or "nothing to remove" in output
