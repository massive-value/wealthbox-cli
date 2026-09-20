from __future__ import annotations

from typing import Any

import typer

from ._util import OutputFormat, handle_errors, output_result, run_client

app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="List Wealthbox teams.",
    no_args_is_help=True,
)

_DEFAULT_FIELDS = ["id", "name", "member_count"]


def summarize_members(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add a ``member_count`` to each record.

    ``/teams`` returns ``members`` as full user objects and ``/user_groups``
    as bare user IDs; either way the useful summary is how many there are.
    The raw ``members`` list is left in place for ``--verbose``.
    """
    return [{**r, "member_count": len(r.get("members") or [])} for r in records]


@app.command("list", help="List teams in the workspace. Use the IDs with `wbox tasks list --assigned-to-team`.")
@handle_errors
def list_teams(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show all fields, including each member"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    result = run_client(token, lambda c: c.list_teams())
    result["teams"] = summarize_members(result.get("teams", []))
    output_result(result, fmt, fields=None if verbose else _DEFAULT_FIELDS)
