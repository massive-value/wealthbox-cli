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


def test_codex_platform_uses_agents_md(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    platforms = {p.id: p for p in detect_platforms()}
    p = platforms["codex"]
    assert p.skill_filename == "AGENTS.md"
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


def test_install_renames_to_agents_md_for_codex(tmp_path):
    template = _make_template(tmp_path)
    platform = Platform(
        id="t", label="t",
        root_dir=tmp_path / "root",
        skill_filename="AGENTS.md",
        requires_project_cwd=False,
    )
    install_skill(platform, template, force=False)
    dest = tmp_path / "root" / "wealthbox-crm"
    assert (dest / "AGENTS.md").exists()
    assert not (dest / "SKILL.md").exists()


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
