from __future__ import annotations

import json
from datetime import datetime, timezone
from importlib.resources import as_file, files
from pathlib import Path

import typer

from ._skill_platforms import (
    Platform,
    SkillInstallError,
    detect_platforms,
    install_skill,
    is_installed,
    skill_dir,
)

app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Install and manage the wealthbox-crm agent skill.",
    no_args_is_help=True,
)


@app.command("list", help="Show where the skill is installed per platform.")
def list_platforms() -> None:
    header = ("platform", "path", "status", "last-bootstrap")
    rows: list[tuple[str, str, str, str]] = []
    for p in detect_platforms():
        dest = skill_dir(p)
        installed = is_installed(p)
        meta_file = dest / "firm" / "_meta.json"
        last_bootstrap = "—"
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text())
                files = meta.get("files", {})
                if files:
                    last_bootstrap = max(files.values())
            except (json.JSONDecodeError, OSError):
                last_bootstrap = "(unreadable)"
        rows.append((
            p.id,
            str(dest),
            "installed" if installed else "not installed",
            last_bootstrap,
        ))

    widths = [
        max(len(r[i]) for r in ([header] + rows))
        for i in range(4)
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
            typer.echo(f"✓ installed to {skill_dir(target)}")

    if not no_bootstrap:
        if typer.confirm("Run 'wbox skills bootstrap' now?", default=True):
            from ._skill_bootstrap import bootstrap_skill_dir
            for target in targets:
                bootstrap_skill_dir(skill_dir(target), token=None, generated_only=False)
                typer.echo(f"✓ bootstrapped {target.id}")


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
            f"✓ bootstrapped {t.id}: wrote {len(result.wrote_generated)} generated files, "
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
        meta_path = skill_dir(t) / "firm" / "_meta.json"
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text())
                ts_values = list(meta.get("files", {}).values())
                if ts_values:
                    oldest = min(datetime.fromisoformat(ts) for ts in ts_values)
                    age_days = (datetime.now(timezone.utc) - oldest).days
                    if age_days > staleness_days:
                        typer.echo(
                            f"! {t.id}: generated files were {age_days} days stale — refreshing now",
                            err=True,
                        )
            except (json.JSONDecodeError, OSError, ValueError):
                pass

        bootstrap_skill_dir(skill_dir(t), token=token, generated_only=True)
        typer.echo(f"✓ refreshed {t.id}")
