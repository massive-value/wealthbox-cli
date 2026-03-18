from __future__ import annotations

import typer

from ._util import OutputFormat, handle_errors, output_result, run_client

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]}, help="Show info about the current authenticated user.")


@app.callback(invoke_without_command=True, help="Show info about the current authenticated user. Use subcommands for more specific info.")
@handle_errors
def get_me(
    ctx: typer.Context,
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    if ctx.invoked_subcommand is not None:
        return
    output_result(run_client(token, lambda c: c.get_me()), fmt)
