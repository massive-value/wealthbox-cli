"""``wbox firm`` — firm-archive operations."""
from __future__ import annotations

from pathlib import Path

import typer

from ..firm import ApplyMode, ArchiveError
from ..firm import apply as _apply
from ..firm import pack as _pack
from ..firm import unpack as _unpack
from ..firm.diff import compute_diff as _compute_diff
from ..firm.diff import format_report as _format_report
from ._skill_paths import firm_dir as _firm_dir
from .skills import _ensure_firm_migrated

app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Firm-archive export/import operations.",
    no_args_is_help=True,
)


@app.command("export")
def export_firm(
    out: Path = typer.Option(
        Path("firm.zip"),
        "--out",
        "-o",
        help="Path to write the firm archive zip. Defaults to ./firm.zip.",
    ),
) -> None:
    """Export the local firm directory as a portable zip archive.

    Only hand-edited policy files and a small policy-shaped subset of
    ``_meta.json`` are included. Generated files (``categories.md``,
    ``custom-fields.md``, ``users.md``) and API-derived metadata
    (refresh timestamps, ``cli_version``) are excluded by construction.
    """
    _ensure_firm_migrated()
    src = _firm_dir()
    if not src.is_dir():
        raise typer.BadParameter(
            f"Firm directory not found at {src}. Run 'wbox skills bootstrap' first."
        )
    blob = _pack(src)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(blob)
    typer.echo(f"Wrote {out} ({len(blob)} bytes).", err=True)


@app.command("import")
def import_firm(
    path: Path = typer.Argument(
        ...,
        help="Path to a firm-archive zip produced by `wbox firm export`.",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip the overwrite confirmation prompt.",
    ),
) -> None:
    """Import a firm-archive zip into the local firm directory (overwrite mode).

    Overwrite is the default — every hand-edited policy file in the archive
    replaces its counterpart in the firm directory. Files in the firm
    directory that aren't in the archive (generated ``categories.md``,
    ``custom-fields.md``, ``users.md``) are left untouched.
    """
    _ensure_firm_migrated()
    try:
        plan = _unpack(path)
    except ArchiveError as exc:
        raise typer.BadParameter(str(exc)) from exc

    dest = _firm_dir()
    if not yes:
        typer.confirm(
            f"Overwrite {len(plan.files)} file(s) in {dest}?",
            abort=True,
        )

    try:
        result = _apply(plan, dest, ApplyMode.OVERWRITE, source=str(path))
    except ArchiveError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"Wrote {len(result.written)} file(s) to {dest}.", err=True)


@app.command("diff")
def diff_firm(
    path: Path = typer.Argument(
        ...,
        help="Path to a firm-archive zip produced by `wbox firm export`.",
    ),
) -> None:
    """Show a unified diff of a firm-archive zip against the local firm directory.

    Output is a summary header (added / modified / removed counts and
    filenames) followed by a per-file unified diff in the same format as
    ``git diff``. Nothing is written to disk — this command is read-only.

    The exit code is ``0`` when the local firm directory matches the
    archive and non-zero when there are changes, so the command is
    pipe-checkable (``wbox firm diff foo.zip || echo drift``).

    ``_meta.json`` is intentionally omitted from the diff because the
    archive carries only the policy-key subset of that file; a bytewise
    diff against the destination's merged meta would always show drift.
    """
    _ensure_firm_migrated()
    try:
        plan = _unpack(path)
    except ArchiveError as exc:
        raise typer.BadParameter(str(exc)) from exc

    report = _compute_diff(plan, _firm_dir())
    typer.echo(_format_report(report), nl=False)
    if report.has_changes:
        raise typer.Exit(code=1)
