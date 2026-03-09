from __future__ import annotations

import typer

from ._util import handle_errors, output_result, run_client

app = typer.Typer(help="Manage Wealthbox users.", no_args_is_help=True)


_DEFAULT_FIELDS = ["id", "name", "email"]


@app.command("list", help="List users.")
@handle_errors
def list_users(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all fields"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    output_result(run_client(token, lambda c: c.list_users()), fmt, fields=None if verbose else _DEFAULT_FIELDS)
