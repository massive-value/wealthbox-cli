from __future__ import annotations

import typer

from ._util import OutputFormat, handle_errors, output_result, run_client
from .teams import summarize_members

app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Manage Wealthbox users.",
    no_args_is_help=True,
)


_DEFAULT_FIELDS = ["id", "name", "email"]


@app.command("list", help="List users.")
@handle_errors
def list_users(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all fields"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    output_result(run_client(token, lambda c: c.list_all_users()), fmt, fields=None if verbose else _DEFAULT_FIELDS)


_GROUP_FIELDS = ["id", "name", "member_count"]


@app.command(
    "groups",
    help="List user groups in the workspace. Group IDs are what `visible_to` accepts.",
)
@handle_errors
def list_user_groups(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all fields, including member IDs"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    result = run_client(token, lambda c: c.list_user_groups())
    result["user_groups"] = summarize_members(result.get("user_groups", []))
    output_result(result, fmt, fields=None if verbose else _GROUP_FIELDS)
