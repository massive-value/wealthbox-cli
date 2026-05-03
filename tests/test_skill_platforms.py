from __future__ import annotations

from pathlib import Path

import pytest

from wealthbox_tools.cli._skill_platforms import (
    Platform,
    detect_platforms,
    skill_dir,
)


def test_claude_code_user_platform_uses_home_claude_skills(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))  # Windows
    platforms = {p.id: p for p in detect_platforms()}
    p = platforms["claude-code-user"]
    assert p.skill_filename == "SKILL.md"
    assert p.root_dir == tmp_path / ".claude" / "skills"
    assert p.requires_project_cwd is False


def test_codex_platform_uses_skill_md(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    platforms = {p.id: p for p in detect_platforms()}
    p = platforms["codex"]
    assert p.skill_filename == "SKILL.md"
    assert p.root_dir == tmp_path / ".codex" / "skills"


def test_claude_code_project_platform_uses_cwd(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    platforms = {p.id: p for p in detect_platforms()}
    p = platforms["claude-code-project"]
    assert p.skill_filename == "SKILL.md"
    assert p.root_dir == tmp_path / ".claude" / "skills"
    assert p.requires_project_cwd is True


def test_skill_dir_appends_wealthbox_crm():
    p = Platform(
        id="test",
        label="Test",
        root_dir=Path("/tmp/test"),
        skill_filename="SKILL.md",
        requires_project_cwd=False,
    )
    assert skill_dir(p) == Path("/tmp/test/wealthbox-crm")


# --------------------------------------------------------------------------- #
# install / uninstall                                                          #
# --------------------------------------------------------------------------- #

from wealthbox_tools.cli._skill_platforms import (  # noqa: E402
    SkillInstallError,
    install_skill,
    is_installed,
    uninstall_skill,
)


def _make_template(tmp_path: Path) -> Path:
    src = tmp_path / "template"
    (src / "references").mkdir(parents=True)
    (src / "SKILL.md").write_text("# hello\n")
    (src / "references" / "contacts.md").write_text("# contacts\n")
    return src


def test_install_copies_template(tmp_path):
    template = _make_template(tmp_path)
    platform = Platform(
        id="t", label="t",
        root_dir=tmp_path / "root",
        skill_filename="SKILL.md",
        requires_project_cwd=False,
    )
    install_skill(platform, template, force=False)
    dest = tmp_path / "root" / "wealthbox-crm"
    assert (dest / "SKILL.md").read_text() == "# hello\n"
    assert (dest / "references" / "contacts.md").exists()
    assert is_installed(platform)


def test_install_keeps_skill_md_for_all_platforms(tmp_path):
    """All platforms (including codex) install SKILL.md verbatim — no rename."""
    template = _make_template(tmp_path)
    platform = Platform(
        id="t", label="t",
        root_dir=tmp_path / "root",
        skill_filename="SKILL.md",
        requires_project_cwd=False,
    )
    install_skill(platform, template, force=False)
    dest = tmp_path / "root" / "wealthbox-crm"
    assert (dest / "SKILL.md").exists()
    assert not (dest / "AGENTS.md").exists()


def test_install_refuses_overwrite_without_force(tmp_path):
    template = _make_template(tmp_path)
    platform = Platform(
        id="t", label="t",
        root_dir=tmp_path / "root",
        skill_filename="SKILL.md",
        requires_project_cwd=False,
    )
    install_skill(platform, template, force=False)
    with pytest.raises(SkillInstallError, match="already installed"):
        install_skill(platform, template, force=False)


def test_install_force_overwrites(tmp_path):
    template = _make_template(tmp_path)
    platform = Platform(
        id="t", label="t",
        root_dir=tmp_path / "root",
        skill_filename="SKILL.md",
        requires_project_cwd=False,
    )
    install_skill(platform, template, force=False)
    (template / "SKILL.md").write_text("# updated\n")
    install_skill(platform, template, force=True)
    assert (tmp_path / "root" / "wealthbox-crm" / "SKILL.md").read_text() == "# updated\n"


def test_uninstall_removes_skill_dir(tmp_path):
    template = _make_template(tmp_path)
    platform = Platform(
        id="t", label="t",
        root_dir=tmp_path / "root",
        skill_filename="SKILL.md",
        requires_project_cwd=False,
    )
    install_skill(platform, template, force=False)
    uninstall_skill(platform)
    assert not is_installed(platform)
    # Parent root_dir still exists
    assert (tmp_path / "root").exists()


def test_uninstall_refuses_nonstandard_path(tmp_path):
    """Path-traversal guard: uninstall must only delete <root>/wealthbox-crm."""
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "important.txt").write_text("don't delete me")

    platform = Platform(
        id="t", label="t",
        root_dir=tmp_path,
        skill_filename="SKILL.md",
        requires_project_cwd=False,
    )
    # Create a symlink at <root>/wealthbox-crm -> <outside>
    target = tmp_path / "wealthbox-crm"
    try:
        target.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unsupported on this platform")
    with pytest.raises(SkillInstallError, match="refusing"):
        uninstall_skill(platform)
    # Outside is untouched
    assert (outside / "important.txt").exists()


# --------------------------------------------------------------------------- #
# Plugin install discovery                                                     #
# --------------------------------------------------------------------------- #

from wealthbox_tools.cli._skill_platforms import detect_plugin_installs  # noqa: E402


def _make_plugin_install(cache_root: Path, marketplace: str, version: str) -> Path:
    """Lay out <cache_root>/<marketplace>/wealthbox-crm/<version>/skills/wealthbox-crm/SKILL.md."""
    skill_dir = cache_root / marketplace / "wealthbox-crm" / version / "skills" / "wealthbox-crm"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# hello\n")
    return skill_dir


def test_detect_plugin_installs_empty_when_no_caches(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    assert detect_plugin_installs() == []


def test_detect_plugin_installs_finds_claude_code_user(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    cache = tmp_path / ".claude" / "plugins" / "cache"
    expected = _make_plugin_install(cache, "massive-value", "1.2.0")
    installs = detect_plugin_installs()
    assert len(installs) == 1
    pi = installs[0]
    assert pi.host == "claude-code-user"
    assert pi.marketplace == "massive-value"
    assert pi.version == "1.2.0"
    assert pi.skill_dir == expected


def test_detect_plugin_installs_finds_codex(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    cache = tmp_path / ".codex" / "plugins" / "cache"
    _make_plugin_install(cache, "openai", "0.9.0")
    installs = detect_plugin_installs()
    assert [pi.host for pi in installs] == ["codex"]


def test_detect_plugin_installs_finds_project_scope(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)
    cache = project / ".claude" / "plugins" / "cache"
    _make_plugin_install(cache, "massive-value", "1.2.0")
    installs = detect_plugin_installs()
    assert [pi.host for pi in installs] == ["claude-code-project"]


def test_detect_plugin_installs_returns_multiple_versions(monkeypatch, tmp_path):
    """A user may have multiple cached versions (claude code keeps old
    versions for rollback). Discovery surfaces every match."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    cache = tmp_path / ".claude" / "plugins" / "cache"
    _make_plugin_install(cache, "massive-value", "1.1.6")
    _make_plugin_install(cache, "massive-value", "1.2.0")
    versions = sorted(pi.version for pi in detect_plugin_installs())
    assert versions == ["1.1.6", "1.2.0"]


def test_detect_plugin_installs_skips_dirs_without_skill_md(monkeypatch, tmp_path):
    """A version dir without skills/wealthbox-crm/SKILL.md isn't a plugin install."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    cache = tmp_path / ".claude" / "plugins" / "cache"
    incomplete = cache / "massive-value" / "wealthbox-crm" / "1.2.0"
    incomplete.mkdir(parents=True)
    # No skills/wealthbox-crm/SKILL.md
    assert detect_plugin_installs() == []


def _write_installed_plugins(plugins_root: Path, install_path: Path, marketplace: str = "massive-value"):
    """Write a host-style installed_plugins.json that marks `install_path` active."""
    plugins_root.mkdir(parents=True, exist_ok=True)
    state = {
        "version": 2,
        "plugins": {
            f"wealthbox-crm@{marketplace}": [
                {
                    "scope": "user",
                    "installPath": str(install_path),
                    "version": install_path.name,
                    "installedAt": "2026-05-03T00:00:00Z",
                    "lastUpdated": "2026-05-03T00:00:00Z",
                    "gitCommitSha": "abc123",
                }
            ]
        },
    }
    (plugins_root / "installed_plugins.json").write_text(__import__("json").dumps(state))


def test_detect_plugin_installs_marks_active_from_installed_plugins_json(monkeypatch, tmp_path):
    """When installed_plugins.json points at a version dir, that install is
    marked active and other cached versions are marked cached."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    plugins_root = tmp_path / ".claude" / "plugins"
    cache = plugins_root / "cache"
    _make_plugin_install(cache, "massive-value", "1.2.0")
    new_install = _make_plugin_install(cache, "massive-value", "1.3.0")
    # installed_plugins.json points at the version-dir root, not the skills/ subdir.
    _write_installed_plugins(plugins_root, new_install.parent.parent)

    installs = {pi.version: pi for pi in detect_plugin_installs()}
    assert installs["1.3.0"].active is True
    assert installs["1.2.0"].active is False


def test_detect_plugin_installs_treats_all_active_when_no_state_file(monkeypatch, tmp_path):
    """No installed_plugins.json -> we have no info, treat every install
    as active rather than pessimistically labeling everything cached."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    cache = tmp_path / ".claude" / "plugins" / "cache"
    _make_plugin_install(cache, "massive-value", "1.3.0")
    # No installed_plugins.json written.
    installs = detect_plugin_installs()
    assert len(installs) == 1
    assert installs[0].active is True
