from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Platform:
    id: str
    label: str
    root_dir: Path
    skill_filename: str
    requires_project_cwd: bool


def _home() -> Path:
    return Path.home()


def detect_platforms() -> list[Platform]:
    home = _home()
    cwd = Path.cwd()
    return [
        Platform(
            id="claude-code-user",
            label="Claude Code (user)",
            root_dir=home / ".claude" / "skills",
            skill_filename="SKILL.md",
            requires_project_cwd=False,
        ),
        Platform(
            id="claude-code-project",
            label="Claude Code (current project)",
            root_dir=cwd / ".claude" / "skills",
            skill_filename="SKILL.md",
            requires_project_cwd=True,
        ),
        Platform(
            id="codex",
            label="Codex",
            root_dir=home / ".codex" / "skills",
            skill_filename="AGENTS.md",
            requires_project_cwd=False,
        ),
    ]


def skill_dir(platform: Platform) -> Path:
    return platform.root_dir / "wealthbox-crm"
