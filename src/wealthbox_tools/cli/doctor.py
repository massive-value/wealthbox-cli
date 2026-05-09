"""Comprehensive health check across the wbox install.

`wbox doctor` and `wbox skills doctor` both call into `run_doctor()` so
the legacy `skills doctor` command keeps working as an alias.
"""
from __future__ import annotations

import os
import platform as _platform_module
import shutil
import sys
from datetime import datetime
from importlib.metadata import version as _pkg_version

import typer

from .. import self_upgrade
from ._config import _config_path, load_config
from ._skill_bootstrap import migrate_legacy_firm, read_firm_meta, read_meta
from ._skill_paths import firm_dir, firm_meta_path
from ._skill_platforms import (
    detect_platforms,
    is_installed,
    skill_dir,
)
from .self_cmd import _default_install_root


def _detect_token_source(token_arg: str | None) -> tuple[str | None, str]:
    """Return (token, source_label) matching get_client's resolution order:
    --token flag > WEALTHBOX_TOKEN env > config file > .env (loaded as env)."""
    if token_arg:
        return token_arg, "--token flag"
    env_token = os.environ.get("WEALTHBOX_TOKEN")
    if env_token:
        return env_token, "env var (WEALTHBOX_TOKEN)"
    cfg = load_config()
    cfg_token = cfg.get("token")
    if cfg_token:
        return cfg_token, f"config file ({_config_path()})"
    try:
        from dotenv import load_dotenv
        load_dotenv()
        dotenv_token = os.environ.get("WEALTHBOX_TOKEN")
        if dotenv_token:
            return dotenv_token, ".env file in working directory"
    except ImportError:
        pass
    return None, "not set"


def run_doctor(token: str | None = None) -> int:
    """Run all health checks. Returns exit code (0 = healthy, 1 = issues found)."""
    issues: list[str] = []

    migrated_from = _ensure_firm_migrated()
    if migrated_from is not None:
        typer.echo(f"! migrated legacy firm/ data from {migrated_from} to {firm_dir()}")
        typer.echo("")

    # --- wbox CLI ---------------------------------------------------------
    typer.echo("# wbox CLI")
    cli_version = _pkg_version("wealthbox-cli")
    py_version = ".".join(str(v) for v in sys.version_info[:3])
    binary = shutil.which("wbox") or "(not on PATH -running via python -m)"
    typer.echo(f"  version:  {cli_version}")
    typer.echo(f"  python:   {py_version} ({_platform_module.system()})")
    typer.echo(f"  binary:   {binary}")

    # --- Authentication ---------------------------------------------------
    typer.echo("\n# Authentication")
    config_path = _config_path()
    if config_path.exists():
        cfg = load_config()
        cfg_token = cfg.get("token", "")
        masked = f"...{cfg_token[-4:]}" if len(cfg_token) > 4 else "****"
        typer.echo(f"  config:   {config_path} (present, masked: {masked})")
    else:
        typer.echo(f"  config:   {config_path} (not present)")
    resolved_token, source = _detect_token_source(token)
    typer.echo(f"  source:   {source}")
    if not resolved_token:
        typer.echo("  smoke:    skipped (no token)")
        issues.append("token not configured - run 'wbox config set-token'")
    else:
        from wealthbox_tools.client import WealthboxAPIError

        from ._util import run_client
        try:
            me = run_client(token, lambda c: c.get_me())
            accounts = me.get("accounts") or []
            firm_name = accounts[0].get("name") if accounts else "(no firm)"
            typer.echo(
                f"  smoke:    OK /me returned {me.get('name')} "
                f"({firm_name}, user {me.get('id')})"
            )
        except WealthboxAPIError as e:
            typer.echo(f"  smoke:    FAILED token rejected by /me: {e}")
            issues.append("token rejected by /me - check it's still valid")
        except Exception as e:
            typer.echo(f"  smoke:    FAILED network/config error: {e}")
            issues.append(f"smoke test failed: {e}")

    # --- Agent CLIs -------------------------------------------------------
    typer.echo("\n# Agent CLIs on PATH")
    claude_path = shutil.which("claude") or shutil.which("claude.exe")
    codex_path = shutil.which("codex") or shutil.which("codex.exe")
    typer.echo(f"  claude:   {claude_path or 'not detected'}")
    typer.echo(f"  codex:    {codex_path or 'not detected'}")

    # --- Skill installs ---------------------------------------------------
    typer.echo("\n# Skill installs")
    for p in detect_platforms():
        status = "installed" if is_installed(p) else "not installed"
        meta = read_meta(skill_dir(p)) if is_installed(p) else {}
        template_v = (meta.get("template") or {}).get("cli_version", "-")
        upgrade_hint = ""
        if template_v not in ("-", cli_version):
            upgrade_hint = f"  [upgrade: {template_v} -> {cli_version}]"
            issues.append(
                f"{p.id} skill template is {template_v}, latest is {cli_version} "
                f"- run 'wbox skills upgrade'"
            )
        typer.echo(
            f"  {p.id:<22} {status:<16} template={template_v:<10} {skill_dir(p)}{upgrade_hint}"
        )

    # --- Firm data --------------------------------------------------------
    typer.echo("\n# Firm data (canonical)")
    typer.echo(f"  path:     {firm_dir()}")
    typer.echo(f"  meta:     {firm_meta_path()}")
    firm_meta = read_firm_meta()
    if not firm_meta:
        typer.echo("  state:    not bootstrapped")
        issues.append("firm data not bootstrapped - run 'wbox skills bootstrap'")
    else:
        identity = firm_meta.get("identity") or {}
        if firm_meta.get("onboarded_at"):
            firm_state = "onboarded"
        else:
            firm_state = "bootstrapped (qualitative pending)"
            issues.append(
                "firm onboarding incomplete - open the skill in your agent to "
                "walk through bootstrap.md (it'll call 'wbox skills mark-onboarded')"
            )
        typer.echo(f"  state:    {firm_state}")
        typer.echo(f"  firm:     {identity.get('name', '-')}")
        typer.echo(f"  user:     {identity.get('user_name', '-')}")
        if firm_dir().exists():
            md_files = sorted(p.name for p in firm_dir().glob("*.md"))
            generated_set = set((firm_meta.get("files") or {}).keys())
            handed = [f for f in md_files if f not in generated_set and not f.startswith("_")]
            typer.echo(
                f"  files:    {len(md_files)} markdown ({len(generated_set)} generated, "
                f"{len(handed)} hand-edited)"
            )
            file_ts = list((firm_meta.get("files") or {}).values())
            if file_ts:
                try:
                    oldest = min(datetime.fromisoformat(t).date() for t in file_ts)
                    typer.echo(f"  oldest:   {oldest}")
                except (ValueError, TypeError):
                    pass

    # --- Release age (30-days-behind warning, #41) -----------------------
    # Soft check: a network error here yields a "could not check for
    # updates" line, never a hard fail. The check is informational —
    # nudge the user if their local version is behind AND the latest
    # release is more than 30 days old.
    typer.echo("\n# Release age")
    typer.echo(f"  local:    {cli_version}")
    staleness = self_upgrade.check_release_staleness()
    if staleness is None:
        typer.echo("  warning:  could not check for updates (network or GitHub error)")
    else:
        typer.echo(f"  latest:   {staleness.latest_version} ({staleness.days_old}d old)")
        if staleness.behind and staleness.days_old > 30:
            typer.echo(
                f"  warning:  local version is behind and the latest release "
                f"({staleness.latest_version}) is {staleness.days_old} days old - "
                f"consider running 'wbox self upgrade'"
            )
            issues.append(
                f"local version {cli_version} is behind {staleness.latest_version} "
                f"({staleness.days_old} days old) - run 'wbox self upgrade'"
            )

    # --- Self-upgrade backups --------------------------------------------
    # Sweep stale `<binary>.old.<ts>` rollback breadcrumbs (#39). Same
    # 24h threshold as `apply()` — doctor is the second sweep so users
    # who haven't upgraded recently still get cleanup. Best-effort: if
    # the install root isn't writable (system-managed install) we
    # report 0 swept rather than failing the doctor.
    typer.echo("\n# Self-upgrade backups")
    install_root = _default_install_root()
    typer.echo(f"  root:     {install_root}")
    try:
        removed = self_upgrade._cleanup_stale_backups(install_root)
        if removed:
            typer.echo(f"  swept:    {len(removed)} stale .old.<ts> files")
        else:
            typer.echo("  swept:    none")
    except OSError as e:
        typer.echo(f"  swept:    skipped ({e})")

    # --- Summary ----------------------------------------------------------
    typer.echo("\n# Summary")
    if not issues:
        typer.echo("  All checks passed.")
        return 0
    typer.echo(f"  {len(issues)} issue(s) found:")
    for i in issues:
        typer.echo(f"    ! {i}")
    return 1


def _ensure_firm_migrated():
    """Migrate legacy firm/ data on first read (idempotent)."""
    installed = [skill_dir(p) for p in detect_platforms() if is_installed(p)]
    return migrate_legacy_firm(installed)


def doctor_cmd(
    token: str | None = typer.Option(
        None, "--token",
        help="Override the API token for the smoke test. Overrides env var, config, .env.",
    ),
) -> None:
    """Run the comprehensive doctor.

    Always exits 0 — issues are surfaced in the Summary section. The doctor
    is informational, not a CI gate. (A future --strict flag could change
    this for scripting.) Token is intentionally NOT bound to
    `envvar=WEALTHBOX_TOKEN` so the doctor can report whether the token came
    from the flag, env var, config file, or .env file.
    """
    run_doctor(token=token)
