from __future__ import annotations

from pathlib import Path

from wealthbox_tools.cli.main import app


def _setup(runner, tmp_path, monkeypatch, *platforms: str) -> tuple[Path, Path]:
    """Install one or more platforms in isolated HOME / cwd dirs."""
    home = tmp_path / "home"
    project = tmp_path / "project"
    home.mkdir(exist_ok=True)
    project.mkdir(exist_ok=True)
    (project / ".git").mkdir(exist_ok=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.chdir(project)
    for plat in platforms:
        result = runner.invoke(
            app, ["skills", "install", "--platform", plat, "--no-bootstrap"]
        )
        assert result.exit_code == 0, result.stdout
    return home, project


def _firm_dir(home: Path, project: Path, platform_id: str) -> Path:
    if platform_id == "codex":
        return home / ".codex" / "skills" / "wealthbox-crm" / "firm"
    if platform_id == "claude-code-user":
        return home / ".claude" / "skills" / "wealthbox-crm" / "firm"
    if platform_id == "claude-code-project":
        return project / ".claude" / "skills" / "wealthbox-crm" / "firm"
    raise ValueError(platform_id)


def test_sync_copies_firm_dir(runner, tmp_path, monkeypatch):
    home, project = _setup(runner, tmp_path, monkeypatch, "codex", "claude-code-project")

    src_firm = _firm_dir(home, project, "codex")
    src_firm.mkdir(parents=True, exist_ok=True)
    (src_firm / "notes.md").write_text("FIRM NOTES SYNCED")
    (src_firm / "_meta.json").write_text('{"firm": {"name": "Acme"}}')

    result = runner.invoke(
        app,
        ["skills", "sync", "-s", "codex", "-t", "claude-code-project", "--yes"],
    )
    assert result.exit_code == 0, result.stdout + (result.stderr or "")

    tgt = _firm_dir(home, project, "claude-code-project")
    assert (tgt / "notes.md").read_text() == "FIRM NOTES SYNCED"
    assert (tgt / "_meta.json").exists()


def test_sync_dry_run_does_not_write(runner, tmp_path, monkeypatch):
    home, project = _setup(runner, tmp_path, monkeypatch, "codex", "claude-code-project")
    src_firm = _firm_dir(home, project, "codex")
    src_firm.mkdir(parents=True, exist_ok=True)
    (src_firm / "notes.md").write_text("SHOULD NOT WRITE")

    result = runner.invoke(
        app,
        ["skills", "sync", "-s", "codex", "-t", "claude-code-project", "--dry-run"],
    )
    assert result.exit_code == 0, result.stdout
    assert "dry-run" in result.stdout
    tgt = _firm_dir(home, project, "claude-code-project")
    assert not (tgt / "notes.md").exists()


def test_sync_errors_when_source_has_no_firm(runner, tmp_path, monkeypatch):
    _setup(runner, tmp_path, monkeypatch, "codex", "claude-code-project")
    # Don't create firm/ in source
    result = runner.invoke(
        app,
        ["skills", "sync", "-s", "codex", "-t", "claude-code-project", "--yes"],
    )
    assert result.exit_code != 0
    output = (result.stdout or "") + (result.stderr or "")
    assert "no firm/" in output.lower()


def test_sync_errors_when_source_equals_target(runner, tmp_path, monkeypatch):
    home, project = _setup(runner, tmp_path, monkeypatch, "codex", "claude-code-project")
    src_firm = _firm_dir(home, project, "codex")
    src_firm.mkdir(parents=True, exist_ok=True)
    (src_firm / "notes.md").write_text("hi")

    result = runner.invoke(
        app,
        ["skills", "sync", "-s", "codex", "-t", "codex", "--yes"],
    )
    assert result.exit_code != 0
    output = (result.stdout or "") + (result.stderr or "")
    assert "same as the source" in output.lower()


def test_sync_errors_when_only_one_platform_installed(runner, tmp_path, monkeypatch):
    _setup(runner, tmp_path, monkeypatch, "codex")
    result = runner.invoke(
        app,
        ["skills", "sync", "-s", "codex", "-t", "claude-code-project", "--yes"],
    )
    assert result.exit_code != 0
    output = (result.stdout or "") + (result.stderr or "")
    assert "at least two" in output.lower()


def test_sync_all_targets_fans_out(runner, tmp_path, monkeypatch):
    home, project = _setup(
        runner, tmp_path, monkeypatch,
        "codex", "claude-code-user", "claude-code-project",
    )
    src_firm = _firm_dir(home, project, "codex")
    src_firm.mkdir(parents=True, exist_ok=True)
    (src_firm / "notes.md").write_text("FANNED OUT")

    result = runner.invoke(
        app,
        ["skills", "sync", "-s", "codex", "--all-targets", "--yes"],
    )
    assert result.exit_code == 0, result.stdout + (result.stderr or "")

    user_target = _firm_dir(home, project, "claude-code-user")
    project_target = _firm_dir(home, project, "claude-code-project")
    assert (user_target / "notes.md").read_text() == "FANNED OUT"
    assert (project_target / "notes.md").read_text() == "FANNED OUT"


def test_sync_rejects_all_targets_with_explicit_target(runner, tmp_path, monkeypatch):
    home, project = _setup(runner, tmp_path, monkeypatch, "codex", "claude-code-project")
    src_firm = _firm_dir(home, project, "codex")
    src_firm.mkdir(parents=True, exist_ok=True)
    (src_firm / "notes.md").write_text("hi")

    result = runner.invoke(
        app,
        [
            "skills", "sync",
            "-s", "codex",
            "-t", "claude-code-project",
            "--all-targets",
            "--yes",
        ],
    )
    assert result.exit_code != 0
    output = (result.stdout or "") + (result.stderr or "")
    assert "mutually exclusive" in output.lower()
