from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

SKILL_NAME = "wealthbox-crm"


@dataclass(frozen=True)
class Platform:
    id: str
    label: str
    root_dir: Path
    skill_filename: str
    requires_project_cwd: bool


@dataclass(frozen=True)
class PluginInstall:
    """A copy of `wealthbox-crm` discovered inside an agent host's plugin cache.

    These are managed by the host CLI (`claude plugin install ...` or the
    Codex equivalent) — `wbox skills install` does not write here, and
    `wbox skills uninstall` does not touch them.

    `active` is True when the host's `installed_plugins.json` has a record
    pointing at this version's installPath. Old/cached versions kept around
    by the host for rollback report active=False. If the host has no
    `installed_plugins.json` (e.g., older Claude Code, or a Codex setup that
    hasn't shipped one yet), `active` defaults to True since we can't tell.
    """
    host: str        # 'claude-code-user' | 'claude-code-project' | 'codex'
    marketplace: str
    version: str
    skill_dir: Path
    active: bool = True


def _home() -> Path:
    return Path.home()


def _read_active_install_paths(plugins_root: Path) -> set[Path] | None:
    """Read <plugins_root>/installed_plugins.json and return the set of
    install-path roots the host considers active across every scope.

    Returns None when no state file exists — caller should treat every
    discovered plugin as active in that case (we don't have enough info
    to differentiate cached vs active).
    """
    state_file = plugins_root / "installed_plugins.json"
    if not state_file.is_file():
        return None
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    active: set[Path] = set()
    for entries in (data.get("plugins") or {}).values():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            install_path = entry.get("installPath")
            if not install_path:
                continue
            try:
                active.add(Path(install_path).resolve())
            except OSError:
                active.add(Path(install_path))
    return active


def _scan_plugin_cache(
    cache_root: Path,
    host: str,
    active_paths: set[Path] | None,
) -> list[PluginInstall]:
    """Find any `<marketplace>/<plugin-name>/<version>/skills/wealthbox-crm/`
    matches under a Claude Code- or Codex-style plugin cache root."""
    if not cache_root.is_dir():
        return []
    out: list[PluginInstall] = []
    for marketplace_dir in cache_root.iterdir():
        if not marketplace_dir.is_dir():
            continue
        plugin_dir = marketplace_dir / SKILL_NAME
        if not plugin_dir.is_dir():
            continue
        for version_dir in plugin_dir.iterdir():
            if not version_dir.is_dir():
                continue
            skill_dir = version_dir / "skills" / SKILL_NAME
            if not (skill_dir / "SKILL.md").is_file():
                continue
            try:
                version_dir_resolved = version_dir.resolve()
            except OSError:
                version_dir_resolved = version_dir
            if active_paths is None:
                is_active = True
            else:
                is_active = version_dir_resolved in active_paths
            out.append(PluginInstall(
                host=host,
                marketplace=marketplace_dir.name,
                version=version_dir.name,
                skill_dir=skill_dir,
                active=is_active,
            ))
    return out


def detect_plugin_installs() -> list[PluginInstall]:
    """Discover every host-managed plugin copy of wealthbox-crm on this
    machine. Includes Claude Code user scope, Claude Code project scope
    (cwd-relative), and Codex.

    Deduped by resolved skill_dir path so a single install isn't reported
    twice when home and cwd point at the same directory (rare in real use,
    common in tests).
    """
    home = _home()
    cwd = Path.cwd()
    candidates = [
        (home / ".claude" / "plugins", "claude-code-user"),
        (cwd / ".claude" / "plugins", "claude-code-project"),
        (home / ".codex" / "plugins", "codex"),
    ]
    installs: list[PluginInstall] = []
    seen: set[Path] = set()
    for plugins_root, host in candidates:
        active_paths = _read_active_install_paths(plugins_root)
        for pi in _scan_plugin_cache(
            plugins_root / "cache", host=host, active_paths=active_paths,
        ):
            try:
                key = pi.skill_dir.resolve()
            except OSError:
                key = pi.skill_dir
            if key in seen:
                continue
            seen.add(key)
            installs.append(pi)
    return installs


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
