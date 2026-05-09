"""``wbox firm`` — firm-archive operations."""
from __future__ import annotations

from pathlib import Path

import typer

from ..firm import ApplyMode, ArchiveError
from ..firm import apply as _apply
from ..firm import pack as _pack
from ..firm import unpack as _unpack
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
    mode: ApplyMode = typer.Option(
        ApplyMode.OVERWRITE,
        "--mode",
        case_sensitive=False,
        help=(
            "How to reconcile the archive with the local firm directory: "
            "'overwrite' (default) replaces every file; 'merge' writes only "
            "files not already present locally; 'abort-on-conflict' refuses "
            "to write anything if any file would be replaced."
        ),
    ),
) -> None:
    """Import a firm-archive zip into the local firm directory.

    The default mode is ``overwrite`` — every hand-edited policy file in the
    archive replaces its counterpart in the firm directory. ``merge`` skips
    files that already exist locally and writes only new ones.
    ``abort-on-conflict`` refuses to write anything if any file in the
    archive would replace an existing local file. Files in the firm
    directory that aren't in the archive (generated ``categories.md``,
    ``custom-fields.md``, ``users.md``) are left untouched in every mode.
    """
    _ensure_firm_migrated()
    try:
        plan = _unpack(path)
    except ArchiveError as exc:
        raise typer.BadParameter(str(exc)) from exc

    dest = _firm_dir()
    if not yes:
        # The verb in the prompt should match the mode, since 'merge' and
        # 'abort-on-conflict' don't actually overwrite anything.
        verb = {
            ApplyMode.OVERWRITE: "Overwrite",
            ApplyMode.MERGE: "Merge",
            ApplyMode.ABORT_ON_CONFLICT: "Import",
        }[mode]
        typer.confirm(
            f"{verb} {len(plan.files)} file(s) in {dest}?",
            abort=True,
        )

    try:
        result = _apply(plan, dest, mode, source=str(path))
    except ArchiveError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"Wrote {len(result.written)} file(s) to {dest}.", err=True)
