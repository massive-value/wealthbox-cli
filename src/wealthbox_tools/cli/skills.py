from __future__ import annotations

import shutil
from datetime import datetime, timezone
from importlib.metadata import version as _pkg_version
from importlib.resources import as_file, files
from pathlib import Path

import typer

from ._skill_bootstrap import copy_firm_meta, read_meta, update_template_meta
from ._skill_platforms import (
    Platform,
    SkillInstallError,
    detect_platforms,
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


@app.command("list", help="Show where the skill is installed per platform.")
def list_platforms() -> None:
    header = ("platform", "path", "status", "template-version", "last-bootstrap")
    rows: list[tuple[str, str, str, str, str]] = []
    for p in detect_platforms():
        dest = skill_dir(p)
        installed = is_installed(p)
        template_version = "-"
        last_bootstrap = "-"
        if installed:
            meta = read_meta(dest)
            template_version = meta.get("template", {}).get("cli_version", "-")
            firm_section = meta.get("firm") or {}
            firm_files = firm_section.get("files") or {}
            if firm_files:
                last_bootstrap = max(firm_files.values())
        rows.append((
            p.id,
            str(dest),
            "installed" if installed else "not installed",
            template_version,
            last_bootstrap,
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

    if not no_bootstrap:
        if typer.confirm("Run 'wbox skills bootstrap' now?", default=True):
            from ._skill_bootstrap import bootstrap_skill_dir
            for target in targets:
                bootstrap_skill_dir(skill_dir(target), token=token, generated_only=False)
                typer.echo(f"OK bootstrapped {target.id}")


@app.command("bootstrap", help="Populate firm/ files from the Wealthbox API.")
def bootstrap_cmd(
    platforms_flag: list[str] = typer.Option(
        [], "--platform", "-p",
        help="Platform id. Default: every installed platform.",
    ),
    generated_only: bool = typer.Option(
        False, "--generated-only",
        help="Only update generated files; never create stubs.",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print planned writes; make no disk changes."
    ),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
) -> None:
    from ._skill_bootstrap import bootstrap_skill_dir

    if platforms_flag:
        targets = _resolve_platforms(platforms_flag)
    else:
        targets = [p for p in detect_platforms() if is_installed(p)]

    if not targets:
        typer.echo(
            "No installed platforms found. Run 'wbox skills install' first.",
            err=True,
        )
        raise typer.Exit(code=2)

    if dry_run:
        for t in targets:
            typer.echo(
                f"[dry-run] would bootstrap {skill_dir(t)} (generated_only={generated_only})"
            )
        return

    for t in targets:
        result = bootstrap_skill_dir(
            skill_dir(t), token=token, generated_only=generated_only
        )
        typer.echo(
            f"OK bootstrapped {t.id}: wrote {len(result.wrote_generated)} generated files, "
            f"{result.wrote_stubs} stubs (firm: {result.firm_identity.get('name')})"
        )


@app.command("refresh", help="Re-fetch generated firm files. Hand-edited files are preserved.")
def refresh_cmd(
    platforms_flag: list[str] = typer.Option([], "--platform", "-p"),
    staleness_days: int = typer.Option(
        30, "--staleness-days", help="Warn if _meta.json older than N days."
    ),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
) -> None:
    from ._skill_bootstrap import bootstrap_skill_dir

    if platforms_flag:
        targets = _resolve_platforms(platforms_flag)
    else:
        targets = [p for p in detect_platforms() if is_installed(p)]

    if not targets:
        typer.echo(
            "No installed platforms found. Run 'wbox skills install' first.",
            err=True,
        )
        raise typer.Exit(code=2)

    for t in targets:
        meta = read_meta(skill_dir(t))
        firm_files = (meta.get("firm") or {}).get("files") or {}
        if firm_files:
            try:
                oldest = min(datetime.fromisoformat(ts) for ts in firm_files.values())
                age_days = (datetime.now(timezone.utc) - oldest).days
                if age_days > staleness_days:
                    typer.echo(
                        f"! {t.id}: generated files were {age_days} days stale - refreshing now",
                        err=True,
                    )
            except ValueError:
                pass

        bootstrap_skill_dir(skill_dir(t), token=token, generated_only=True)
        typer.echo(f"OK refreshed {t.id}")


@app.command(
    "upgrade",
    help="Refresh template files (SKILL.md, references/, firm-examples/, bootstrap.md) "
         "in every installed platform. Preserves firm/ and _meta.json firm section.",
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


@app.command("doctor", help="Diagnose install state and token.")
def doctor_cmd(
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
) -> None:
    from wealthbox_tools.client import WealthboxAPIError

    from ._util import run_client

    current = _pkg_version("wealthbox-cli")
    typer.echo("# Skill install state")
    for p in detect_platforms():
        status = "installed" if is_installed(p) else "not installed"
        meta = read_meta(skill_dir(p)) if is_installed(p) else {}
        bootstrapped = "bootstrapped" if meta.get("firm") else "not bootstrapped"
        template_v = (meta.get("template") or {}).get("cli_version", "-")
        upgrade_hint = ""
        if template_v not in ("-", current):
            upgrade_hint = f"  [upgrade available: {template_v} -> {current}]"
        typer.echo(
            f"  {p.id:<22} {status:<16} {bootstrapped:<18} "
            f"template={template_v:<10} {skill_dir(p)}{upgrade_hint}"
        )

    typer.echo("\n# Token")
    try:
        me = run_client(token, lambda c: c.get_me())
        accounts = me.get("accounts") or []
        firm_name = accounts[0].get("name") if accounts else "(no firm)"
        typer.echo(
            f"  token ok - authenticated as {me.get('name')} "
            f"(firm: {firm_name}, user id={me.get('id')})"
        )
    except WealthboxAPIError as e:
        typer.echo(f"  token failed: {e}")
    except Exception as e:  # network, config, etc.
        typer.echo(f"  token check failed: {e}")


def _prompt_sync_source(installed: list[Platform]) -> Platform:
    typer.echo("Installed platforms:")
    for i, p in enumerate(installed, 1):
        typer.echo(f"  {i}. {p.id:<22} {p.label}")
    while True:
        raw = typer.prompt("Source platform (id or number)").strip()
        for i, p in enumerate(installed, 1):
            if raw == str(i) or raw == p.id:
                return p
        typer.echo(f"  ! unknown selection {raw!r}; try again", err=True)


def _prompt_sync_targets(candidates: list[Platform]) -> list[Platform]:
    typer.echo("Available targets:")
    for i, p in enumerate(candidates, 1):
        typer.echo(f"  {i}. {p.id:<22} {p.label}")
    typer.echo("  a. all of the above")
    raw = typer.prompt("Targets (comma-separated ids/numbers, or 'a')").strip()
    if raw.lower() in {"a", "all"}:
        return list(candidates)
    selected: list[Platform] = []
    for token in (t.strip() for t in raw.split(",") if t.strip()):
        match: Platform | None = None
        for i, p in enumerate(candidates, 1):
            if token == str(i) or token == p.id:
                match = p
                break
        if match is None:
            raise typer.BadParameter(f"unknown target {token!r}")
        if match not in selected:
            selected.append(match)
    return selected


@app.command(
    "sync",
    help="Copy firm/ files from one installed platform to one or more others.",
)
def sync_cmd(
    source_id: str | None = typer.Option(
        None, "--source", "-s",
        help="Platform id to copy firm/ from. Prompts if omitted.",
    ),
    target_ids: list[str] = typer.Option(
        [], "--target", "-t",
        help="Platform id to copy firm/ to. Repeat for multiple. Prompts if omitted.",
    ),
    all_targets: bool = typer.Option(
        False, "--all-targets",
        help="Sync to every installed platform except the source.",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Show planned writes without copying.",
    ),
    yes: bool = typer.Option(
        False, "--yes", "-y", help="Skip confirmation prompt.",
    ),
) -> None:
    installed = [p for p in detect_platforms() if is_installed(p)]
    if len(installed) < 2:
        ids = [p.id for p in installed] or ["none"]
        typer.echo(
            f"Need at least two installed platforms to sync. Installed: {ids}",
            err=True,
        )
        raise typer.Exit(code=2)

    if source_id:
        source = _resolve_platforms([source_id])[0]
        if not is_installed(source):
            typer.echo(f"Error: source {source.id!r} is not installed.", err=True)
            raise typer.Exit(code=2)
    else:
        source = _prompt_sync_source(installed)

    src_firm = skill_dir(source) / "firm"
    if not src_firm.is_dir():
        typer.echo(
            f"Error: {source.id} has no firm/ directory at {src_firm}. "
            f"Run 'wbox skills bootstrap --platform {source.id}' first.",
            err=True,
        )
        raise typer.Exit(code=2)

    src_resolved = skill_dir(source).resolve()

    def _is_same_path(p: Platform) -> bool:
        return skill_dir(p).resolve() == src_resolved

    others = [p for p in installed if p.id != source.id and not _is_same_path(p)]

    if all_targets and target_ids:
        typer.echo("Error: --all-targets and --target are mutually exclusive.", err=True)
        raise typer.Exit(code=2)

    if all_targets:
        targets = others
    elif target_ids:
        targets = _resolve_platforms(target_ids)
        for t in targets:
            if t.id == source.id or _is_same_path(t):
                typer.echo(
                    f"Error: target {t.id!r} is the same as the source "
                    f"(resolves to {src_resolved}).",
                    err=True,
                )
                raise typer.Exit(code=2)
            if not is_installed(t):
                typer.echo(f"Error: target {t.id!r} is not installed.", err=True)
                raise typer.Exit(code=2)
    else:
        targets = _prompt_sync_targets(others)

    if not targets:
        typer.echo("No targets selected.", err=True)
        raise typer.Exit(code=2)

    typer.echo(f"Source: {source.id} ({src_firm})")
    typer.echo("Targets:")
    for t in targets:
        typer.echo(f"  {t.id} ({skill_dir(t) / 'firm'})")

    src_files = sorted(p for p in src_firm.rglob("*") if p.is_file())

    if dry_run:
        for t in targets:
            tgt_firm = skill_dir(t) / "firm"
            for src_file in src_files:
                rel = src_file.relative_to(src_firm)
                dest = tgt_firm / rel
                action = "overwrite" if dest.exists() else "create"
                typer.echo(f"  [dry-run][{t.id}] {action} firm/{rel.as_posix()}")
        return

    if not yes and not typer.confirm("Proceed with sync?", default=False):
        typer.echo("Cancelled.")
        raise typer.Exit(code=1)

    for t in targets:
        tgt_firm = skill_dir(t) / "firm"
        tgt_firm.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_firm, tgt_firm, dirs_exist_ok=True)
        meta_copied = copy_firm_meta(skill_dir(source), skill_dir(t))
        meta_note = "" if meta_copied else " (no _meta.json firm section on source)"
        typer.echo(
            f"OK synced {len(src_files)} files: {source.id} -> {t.id}{meta_note}"
        )


@app.command("uninstall", help="Remove the wealthbox-crm skill from a platform.")
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
