"""``wbox firm`` — firm-archive operations."""
from __future__ import annotations

from pathlib import Path

import typer

from ..firm import pack as _pack
from ._skill_paths import firm_dir as _firm_dir

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
    src = _firm_dir()
    if not src.is_dir():
        raise typer.BadParameter(
            f"Firm directory not found at {src}. Run 'wbox skills bootstrap' first."
        )
    blob = _pack(src)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(blob)
    typer.echo(f"Wrote {out} ({len(blob)} bytes).", err=True)
