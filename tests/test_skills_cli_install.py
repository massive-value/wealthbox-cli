from __future__ import annotations

from wealthbox_tools.cli.main import app


def test_install_by_flag_copies_template(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app, ["skills", "install", "--platform", "claude-code-user", "--no-bootstrap"]
    )
    assert result.exit_code == 0, result.stdout
    dest = tmp_path / ".claude" / "skills" / "wealthbox-crm"
    assert (dest / "SKILL.md").exists()
    assert (dest / "references" / "contacts.md").exists()
    assert (dest / "bootstrap.md").exists()
    assert (dest / "firm-examples" / "contacts.md").exists()


def test_install_codex_renames_to_agents_md(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app, ["skills", "install", "--platform", "codex", "--no-bootstrap"]
    )
    assert result.exit_code == 0, result.stdout
    dest = tmp_path / ".codex" / "skills" / "wealthbox-crm"
    assert (dest / "AGENTS.md").exists()
    assert not (dest / "SKILL.md").exists()


def test_install_refuses_existing_without_force(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    runner.invoke(
        app, ["skills", "install", "--platform", "claude-code-user", "--no-bootstrap"]
    )
    result = runner.invoke(
        app, ["skills", "install", "--platform", "claude-code-user", "--no-bootstrap"]
    )
    assert result.exit_code != 0
    output = (result.stdout or "") + (result.stderr or "")
    assert "already installed" in output.lower()


def test_install_force_overwrites(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    runner.invoke(
        app, ["skills", "install", "--platform", "claude-code-user", "--no-bootstrap"]
    )
    dest = tmp_path / ".claude" / "skills" / "wealthbox-crm"
    (dest / "SKILL.md").write_text("TAMPERED")
    result = runner.invoke(
        app,
        [
            "skills", "install",
            "--platform", "claude-code-user",
            "--no-bootstrap", "--force",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert (dest / "SKILL.md").read_text().startswith("---")


def test_install_project_scope_requires_git_or_claude(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        ["skills", "install", "--platform", "claude-code-project", "--no-bootstrap"],
    )
    assert result.exit_code != 0


def test_install_project_scope_allowed_with_git(runner, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    (tmp_path / ".git").mkdir()
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        ["skills", "install", "--platform", "claude-code-project", "--no-bootstrap"],
    )
    assert result.exit_code == 0, result.stdout
    assert (tmp_path / ".claude" / "skills" / "wealthbox-crm" / "SKILL.md").exists()
