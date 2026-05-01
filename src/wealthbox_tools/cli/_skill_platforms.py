from __future__ import annotations

import shutil
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
            skill_filename="SKILL.md",
            requires_project_cwd=False,
        ),
    ]


def skill_dir(platform: Platform) -> Path:
    return platform.root_dir / "wealthbox-crm"


class SkillInstallError(Exception):
    """Raised when a skill install/uninstall cannot proceed safely."""


def is_installed(platform: Platform) -> bool:
    dest = skill_dir(platform)
    return dest.is_dir() and (dest / platform.skill_filename).is_file()


def install_skill(platform: Platform, src: Path, *, force: bool) -> None:
    dest = skill_dir(platform)
    if dest.exists() and not force:
        raise SkillInstallError(
            f"Skill already installed at {dest} (use --force to overwrite)"
        )
    if dest.exists():
        _safe_rmtree(platform, dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest)


def upgrade_skill(platform: Platform, src: Path) -> None:
    """Re-copy the bundled template over an existing install.

    Preserves the user's `firm/` directory and root `_meta.json` (the
    bundled template ships neither). Refreshes SKILL.md, references/,
    firm-examples/, and bootstrap.md.
    """
    dest = skill_dir(platform)
    if not dest.is_dir() or not (dest / platform.skill_filename).is_file():
        raise SkillInstallError(
            f"Cannot upgrade: nothing installed at {dest}"
        )
    shutil.copytree(src, dest, dirs_exist_ok=True)


def uninstall_skill(platform: Platform) -> None:
    dest = skill_dir(platform)
    if not dest.exists():
        return
    _safe_rmtree(platform, dest)


def _safe_rmtree(platform: Platform, target: Path) -> None:
    root = platform.root_dir.resolve()
    try:
        resolved = target.resolve(strict=True)
    except FileNotFoundError:
        return
    # Guard: resolved target must sit inside resolved root AND end with "wealthbox-crm".
    if resolved.name != "wealthbox-crm" or root not in resolved.parents:
        raise SkillInstallError(
            f"refusing to remove {resolved}: not a standard skill path under {root}"
        )
    shutil.rmtree(resolved)
