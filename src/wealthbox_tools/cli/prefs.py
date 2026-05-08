"""User-preferences (L3) commands.

The L3 user layer lives at ``~/.config/wbox/user/preferences.md`` (or
``%APPDATA%\\wbox\\user\\preferences.md`` on Windows) — a sibling of the
L2 firm directory. The file is hand-edited; in v2 there is no schema and
``wbox`` never writes to it implicitly. Agents may read it via these
commands and (with user confirmation) edit it directly.
"""
from __future__ import annotations

import sys

import typer

from ._config import _user_prefs_path

app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Read the user-preferences file (~/.config/wbox/user/preferences.md).",
    no_args_is_help=True,
)


@app.command("path", help="Print the absolute path to preferences.md.")
def path_cmd() -> None:
    typer.echo(str(_user_prefs_path()))


@app.command(
    "show",
    help=(
        "Print the contents of preferences.md. "
        "Exits 0 with empty output if the file or its parent directory "
        "is absent — the file is optional."
    ),
)
def show_cmd() -> None:
    prefs_path = _user_prefs_path()
    if not prefs_path.exists():
        return
    # Stream raw bytes to stdout to preserve the file's exact contents
    # (including trailing newlines and encoding) without typer's nl=True
    # appending an extra newline.
    sys.stdout.write(prefs_path.read_text(encoding="utf-8"))
