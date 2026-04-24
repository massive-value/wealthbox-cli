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
