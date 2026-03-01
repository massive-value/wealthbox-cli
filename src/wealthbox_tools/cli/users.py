from __future__ import annotations

import typer

from ._util import handle_errors, output_result, run_client

app = typer.Typer(help="Manage Wealthbox users.", no_args_is_help=True)


@app.command("list")
@handle_errors
def list_users(
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format"),
) -> None:
    """List users."""
    output_result(run_client(token, lambda c: c.list_users()), fmt)
