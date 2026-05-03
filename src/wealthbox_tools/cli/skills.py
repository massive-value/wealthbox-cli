from __future__ import annotations

from datetime import datetime, timezone
from importlib.metadata import version as _pkg_version
from importlib.resources import as_file, files
from pathlib import Path

import typer

from ._skill_bootstrap import (
    mark_firm_onboarded,
    migrate_legacy_firm,
    read_firm_meta,
    read_meta,
    update_template_meta,
)
from ._skill_paths import firm_dir
from ._skill_platforms import (
    Platform,
    SkillInstallError,
    detect_platforms,
    detect_plugin_installs,
    install_skill,
    is_installed,
    skill_dir,
    uninstall_skill,
    upgrade_skill,
)

app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Install and manage the wealthbox-crm agent skill.",
    no_args_is_help=True,
)


def _ensure_firm_migrated() -> Path | None:
    """Migrate legacy `<skill_dir>/firm/` data to the canonical path if needed.

    Idempotent — a no-op once canonical firm meta exists. Returns the source
    skill dir migrated from, or None if nothing migrated.
    """
    installed = [skill_dir(p) for p in detect_platforms() if is_installed(p)]
    return migrate_legacy_firm(installed)


@app.command("list", help="Show every skill copy on this machine: legacy installs and plugin-managed.")
def list_platforms() -> None:
    _ensure_firm_migrated()
    firm_meta = read_firm_meta()
    last_bootstrap = "-"
    onboarded = "no"
    if firm_meta:
        files_map = firm_meta.get("files") or {}
        if files_map:
            last_bootstrap = max(files_map.values())
        onboarded = firm_meta.get("onboarded_at") or "no"

    header = ("source", "path", "status", "version")
    rows: list[tuple[str, str, str, str]] = []
    for p in detect_platforms():
        dest = skill_dir(p)
        installed = is_installed(p)
        template_version = "-"
        if installed:
            template_version = (read_meta(dest).get("template") or {}).get("cli_version", "-")
        rows.append((
            p.id,
            str(dest),
            "installed" if installed else "not installed",
            template_version,
        ))
    for pi in detect_plugin_installs():
        rows.append((
            f"plugin:{pi.host}",
            str(pi.skill_dir),
            f"plugin@{pi.marketplace}",
            pi.version,
        ))

    widths = [
        max(len(r[i]) for r in ([header] + rows))
        for i in range(len(header))
    ]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    typer.echo(fmt.format(*header))
    typer.echo(fmt.format(*("-" * w for w in widths)))
    for r in rows:
        typer.echo(fmt.format(*r))

    typer.echo("")
    typer.echo(f"firm-path:       {firm_dir()}")
    typer.echo(f"last-bootstrap:  {last_bootstrap}")
    typer.echo(f"onboarded:       {onboarded}")


def _resolve_platforms(ids: list[str]) -> list[Platform]:
    """Translate --platform flags to Platform objects; validate they exist."""
    known = {p.id: p for p in detect_platforms()}
    selected: list[Platform] = []
    for pid in ids:
        if pid not in known:
            raise typer.BadParameter(
                f"unknown platform {pid!r}; choose from {sorted(known)}"
            )
        selected.append(known[pid])
    return selected


def _project_scope_allowed() -> bool:
    cwd = Path.cwd()
    return (cwd / ".git").exists() or (cwd / ".claude").exists()


def _prompt_platforms() -> list[Platform]:
    available = detect_platforms()
    typer.echo("Select platforms (comma-separated ids):")
    for p in available:
        typer.echo(f"  {p.id:<22} {p.label:<32} {p.root_dir}")
    raw = typer.prompt("platforms", default="claude-code-user")
    ids = [x.strip() for x in raw.split(",") if x.strip()]
    return _resolve_platforms(ids)


@app.command("install", help="Install the wealthbox-crm skill to a platform.")
def install_cmd(
    platforms_flag: list[str] = typer.Option(
        [], "--platform", "-p",
        help="Platform id: claude-code-user | claude-code-project | codex. Repeat to install to multiple.",
    ),
    force: bool = typer.Option(False, "--force", help="Overwrite existing install."),
    no_bootstrap: bool = typer.Option(False, "--no-bootstrap", help="Skip the post-install bootstrap prompt."),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
) -> None:
    targets = _resolve_platforms(platforms_flag) if platforms_flag else _prompt_platforms()

    if any(t.requires_project_cwd for t in targets) and not _project_scope_allowed():
        typer.echo(
            "Error: claude-code-project requires the current directory to contain .git or .claude",
            err=True,
        )
        raise typer.Exit(code=2)

    with as_file(files("wealthbox_tools").joinpath("skills/wealthbox-crm")) as src:
        for target in targets:
            try:
                install_skill(target, Path(src), force=force)
            except SkillInstallError as e:
                typer.echo(f"Error installing to {target.id}: {e}", err=True)
                raise typer.Exit(code=1) from e
            update_template_meta(skill_dir(target), cli_version=_pkg_version("wealthbox-cli"))
            typer.echo(f"OK installed to {skill_dir(target)}")

    _ensure_firm_migrated()

    if not no_bootstrap:
        if typer.confirm("Run 'wbox skills bootstrap' now?", default=True):
            from ._skill_bootstrap import bootstrap_firm
            bootstrap_firm(token=token, generated_only=False)
            typer.echo(f"OK bootstrapped firm at {firm_dir()}")


@app.command(
    "bootstrap",
    help="Populate firm data from the Wealthbox API. Writes to one canonical location per machine.",
)
def bootstrap_cmd(
    platforms_flag: list[str] = typer.Option(
        [], "--platform", "-p",
        help="Deprecated: firm data is now machine-level, no longer per-platform. The flag is accepted but ignored.",
    ),
    generated_only: bool = typer.Option(
        False, "--generated-only",
        help="Only update generated files; never create stubs.",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print the planned target; make no disk changes."
    ),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
) -> None:
    from ._skill_bootstrap import bootstrap_firm

    if platforms_flag:
        typer.echo(
            "! --platform is deprecated and ignored; firm data is now machine-level.",
            err=True,
        )

    _ensure_firm_migrated()

    if dry_run:
        typer.echo(f"[dry-run] would bootstrap {firm_dir()} (generated_only={generated_only})")
        return

    result = bootstrap_firm(token=token, generated_only=generated_only)
    typer.echo(
        f"OK bootstrapped {result.firm_dir}: wrote {len(result.wrote_generated)} generated files, "
        f"{result.wrote_stubs} stubs (firm: {result.firm_identity.get('name')})"
    )


@app.command("refresh", help="Re-fetch generated firm files. Hand-edited files are preserved.")
def refresh_cmd(
    platforms_flag: list[str] = typer.Option(
        [], "--platform", "-p",
        help="Deprecated: firm data is now machine-level, no longer per-platform.",
    ),
    staleness_days: int = typer.Option(
        30, "--staleness-days", help="Warn if firm meta older than N days."
    ),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
) -> None:
    from ._skill_bootstrap import bootstrap_firm

    if platforms_flag:
        typer.echo(
            "! --platform is deprecated and ignored; firm data is now machine-level.",
            err=True,
        )

    _ensure_firm_migrated()

    meta = read_firm_meta()
    if not meta:
        typer.echo(
            "No firm data found. Run 'wbox skills bootstrap' first.",
            err=True,
        )
        raise typer.Exit(code=2)

    files_map = meta.get("files") or {}
    if files_map:
        try:
            oldest = min(datetime.fromisoformat(ts) for ts in files_map.values())
            age_days = (datetime.now(timezone.utc) - oldest).days
            if age_days > staleness_days:
                typer.echo(
                    f"! generated files were {age_days} days stale - refreshing now",
                    err=True,
                )
        except ValueError:
            pass

    bootstrap_firm(token=token, generated_only=True)
    typer.echo(f"OK refreshed {firm_dir()}")


@app.command(
    "upgrade",
    help="Refresh template files (SKILL.md, references/, firm-examples/, bootstrap.md) "
         "in every installed platform. Firm data is unaffected (it lives outside the skill dir).",
)
def upgrade_cmd(
    platforms_flag: list[str] = typer.Option(
        [], "--platform", "-p",
        help="Platform id. Default: every installed platform.",
    ),
) -> None:
    if platforms_flag:
        targets = _resolve_platforms(platforms_flag)
        for t in targets:
            if not is_installed(t):
                typer.echo(f"Error: {t.id!r} is not installed.", err=True)
                raise typer.Exit(code=2)
    else:
        targets = [p for p in detect_platforms() if is_installed(p)]

    if not targets:
        typer.echo(
            "No installed platforms found. Run 'wbox skills install' first.",
            err=True,
        )
        raise typer.Exit(code=2)

    current = _pkg_version("wealthbox-cli")

    with as_file(files("wealthbox_tools").joinpath("skills/wealthbox-crm")) as src:
        for t in targets:
            existing = (read_meta(skill_dir(t)).get("template") or {}).get("cli_version", "-")
            try:
                upgrade_skill(t, Path(src))
            except SkillInstallError as e:
                typer.echo(f"Error upgrading {t.id}: {e}", err=True)
                raise typer.Exit(code=1) from e
            update_template_meta(skill_dir(t), cli_version=current)
            typer.echo(f"OK upgraded {t.id}: {existing} -> {current}")


@app.command(
    "doctor",
    help="Diagnose install state, auth, and firm data. Alias of `wbox doctor`.",
)
def doctor_cmd(
    token: str | None = typer.Option(
        None, "--token",
        help="Override the API token for the smoke test.",
    ),
) -> None:
    # `wbox skills doctor` is the older entry point; `wbox doctor` is the
    # canonical top-level form. Both call the same function so the output
    # never drifts. Token is intentionally not bound to envvar= so the
    # doctor can report whether the token came from the flag, env var,
    # config file, or .env file.
    from .doctor import run_doctor
    run_doctor(token=token)


@app.command(
    "firm-path",
    help="Print the canonical firm data directory. Use this from agents to find firm/ files.",
)
def firm_path_cmd() -> None:
    _ensure_firm_migrated()
    typer.echo(str(firm_dir()))


@app.command(
    "mark-onboarded",
    help="Stamp `onboarded_at` in canonical firm meta. Run after qualitative firm Q&A is captured.",
)
def mark_onboarded_cmd(
    platforms_flag: list[str] = typer.Option(
        [], "--platform", "-p",
        help="Deprecated: onboarded_at is now machine-level, no longer per-platform.",
    ),
) -> None:
    if platforms_flag:
        typer.echo(
            "! --platform is deprecated and ignored; onboarded_at is now machine-level.",
            err=True,
        )

    _ensure_firm_migrated()

    try:
        ts = mark_firm_onboarded()
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=2) from e
    typer.echo(f"OK marked onboarded at {ts}")


@app.command("uninstall", help="Remove the wealthbox-crm skill from a platform. Firm data is preserved.")
def uninstall_cmd(
    platforms_flag: list[str] = typer.Option([], "--platform", "-p"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    if platforms_flag:
        targets = _resolve_platforms(platforms_flag)
    else:
        targets = [p for p in detect_platforms() if is_installed(p)]
        if not targets:
            typer.echo("Nothing to remove. No installed platforms detected.")
            return

    for t in targets:
        if not is_installed(t):
            typer.echo(f"  {t.id}: not installed, skipping")
            continue
        if not yes and not typer.confirm(f"Remove {skill_dir(t)}?", default=False):
            continue
        try:
            uninstall_skill(t)
            typer.echo(f"OK removed {skill_dir(t)}")
        except SkillInstallError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(code=1) from e
