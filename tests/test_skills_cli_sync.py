from __future__ import annotations

import json
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
    (src_firm / "categories.md").write_text("# generated categories\n")

    result = runner.invoke(
        app,
        ["skills", "sync", "-s", "codex", "-t", "claude-code-project", "--yes"],
    )
    assert result.exit_code == 0, result.stdout + (result.stderr or "")

    tgt = _firm_dir(home, project, "claude-code-project")
    assert (tgt / "notes.md").read_text() == "FIRM NOTES SYNCED"
    assert (tgt / "categories.md").exists()


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


def _skill_root(home: Path, project: Path, platform_id: str) -> Path:
    return _firm_dir(home, project, platform_id).parent


def test_sync_propagates_firm_meta_section(runner, tmp_path, monkeypatch):
    """After sync, the target's _meta.json should carry the source's firm section
    so the SKILL.md first-run gate doesn't trigger another bootstrap."""
    home, project = _setup(runner, tmp_path, monkeypatch, "codex", "claude-code-project")

    src_root = _skill_root(home, project, "codex")
    src_firm = src_root / "firm"
    src_firm.mkdir(parents=True, exist_ok=True)
    (src_firm / "categories.md").write_text("# generated\n")

    src_meta = {
        "template": {"cli_version": "1.1.2"},
        "firm": {
            "identity": {"id": 42, "name": "Acme Wealth"},
            "cli_version": "1.1.2",
            "files": {"categories.md": "2026-05-01T00:00:00+00:00"},
        },
    }
    (src_root / "_meta.json").write_text(json.dumps(src_meta))

    tgt_root = _skill_root(home, project, "claude-code-project")
    tgt_meta = {"template": {"cli_version": "1.1.2"}}
    (tgt_root / "_meta.json").write_text(json.dumps(tgt_meta))

    result = runner.invoke(
        app,
        ["skills", "sync", "-s", "codex", "-t", "claude-code-project", "--yes"],
    )
    assert result.exit_code == 0, result.stdout + (result.stderr or "")

    written = json.loads((tgt_root / "_meta.json").read_text())
    assert written["firm"] == src_meta["firm"]
    assert written["template"] == {"cli_version": "1.1.2"}


def test_sync_notes_when_source_has_no_firm_meta(runner, tmp_path, monkeypatch):
    """If the source has no firm section yet, sync should still succeed but flag it."""
    home, project = _setup(runner, tmp_path, monkeypatch, "codex", "claude-code-project")
    src_firm = _firm_dir(home, project, "codex")
    src_firm.mkdir(parents=True, exist_ok=True)
    (src_firm / "categories.md").write_text("# generated\n")

    result = runner.invoke(
        app,
        ["skills", "sync", "-s", "codex", "-t", "claude-code-project", "--yes"],
    )
    assert result.exit_code == 0, result.stdout + (result.stderr or "")
    assert "no _meta.json firm section" in result.stdout.lower()


def test_sync_rejects_target_resolving_to_same_path(runner, tmp_path, monkeypatch):
    """When cwd == HOME, claude-code-user and claude-code-project resolve to the
    same skill dir; sync must refuse instead of running shutil.copytree on itself."""
    home = tmp_path / "home"
    home.mkdir()
    (home / ".git").mkdir()  # satisfy _project_scope_allowed when cwd == home
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.chdir(home)

    install_user = runner.invoke(
        app, ["skills", "install", "--platform", "claude-code-user", "--no-bootstrap"]
    )
    assert install_user.exit_code == 0, install_user.stdout

    user_skill = home / ".claude" / "skills" / "wealthbox-crm"
    project_skill = home / ".claude" / "skills" / "wealthbox-crm"
    assert user_skill.resolve() == project_skill.resolve()

    src_firm = user_skill / "firm"
    src_firm.mkdir(parents=True, exist_ok=True)
    (src_firm / "categories.md").write_text("# generated\n")

    result = runner.invoke(
        app,
        [
            "skills", "sync",
            "-s", "claude-code-user",
            "-t", "claude-code-project",
            "--yes",
        ],
    )
    assert result.exit_code != 0
    output = (result.stdout or "") + (result.stderr or "")
    assert "same as the source" in output.lower()


def test_sync_all_targets_skips_same_path_collision(runner, tmp_path, monkeypatch):
    """--all-targets must filter out platforms whose skill dir resolves to the source's."""
    home = tmp_path / "home"
    home.mkdir()
    (home / ".git").mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.chdir(home)

    runner.invoke(app, ["skills", "install", "--platform", "claude-code-user", "--no-bootstrap"])
    runner.invoke(app, ["skills", "install", "--platform", "codex", "--no-bootstrap"])

    src_firm = home / ".claude" / "skills" / "wealthbox-crm" / "firm"
    src_firm.mkdir(parents=True, exist_ok=True)
    (src_firm / "categories.md").write_text("# generated\n")

    result = runner.invoke(
        app,
        ["skills", "sync", "-s", "claude-code-user", "--all-targets", "--yes"],
    )
    assert result.exit_code == 0, result.stdout + (result.stderr or "")
    # codex should be the only synced target; claude-code-project must be filtered out.
    assert "-> codex" in result.stdout
    assert "-> claude-code-project" not in result.stdout


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
