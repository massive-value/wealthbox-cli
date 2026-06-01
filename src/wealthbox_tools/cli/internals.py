"""Hidden ``wbox internals`` sub-app for repo maintenance commands.

Commands here are not part of the public CLI surface; they are excluded
from ``wbox --help`` via ``hidden=True`` and exist for tasks like
regenerating skill reference docs from the live Typer command tree.
"""
from __future__ import annotations

import typer

app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Repo-maintenance commands (hidden from --help).",
    no_args_is_help=True,
    hidden=True,
)


@app.command(
    "regen-skill-refs",
    help="Regenerate flag tables in skill reference markdown files from the Typer command tree.",
    hidden=True,
)
def regen_skill_refs() -> None:
    from wealthbox_tools.internals.skill_ref_gen import regenerate_all

    result = regenerate_all()
    for path in result.modified:
        typer.echo(f"updated {path}")
    for path in result.skipped_no_markers:
        typer.echo(f"skipped (no markers) {path}", err=True)
    for path in result.missing:
        typer.echo(f"missing {path}", err=True)
    for path in result.unmapped:
        typer.echo(f"unmapped (no resource binding) {path}", err=True)
    if not result.modified:
        typer.echo("no changes")
