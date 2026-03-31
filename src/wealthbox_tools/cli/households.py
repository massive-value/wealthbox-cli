from __future__ import annotations

import typer

from wealthbox_tools.models import HouseholdMemberInput, HouseholdTitle

from ._util import OutputFormat, handle_errors, output_result, run_client

app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Manage household members.",
    no_args_is_help=True,
)


@app.command(
    "add-member",
    help="Add a member to a household. Usage: add-member <household_id> <member_id> --title <title>",
)
@handle_errors
def add_member(
    household_id: int = typer.Argument(..., help="Household contact ID"),
    member_id: int = typer.Argument(..., help="Member contact ID to add"),
    title: HouseholdTitle = typer.Option(..., help="Household title for member (e.g. Spouse, Head)"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    payload = HouseholdMemberInput(id=member_id, title=title)
    
    output_result(run_client(token, lambda c: c.add_household_member(household_id, payload)), fmt)


@app.command("remove-member", help="Remove a member from a household.")
@handle_errors
def remove_member(
    household_id: int = typer.Argument(..., help="Household contact ID"),
    member_id: int = typer.Argument(..., help="Member contact ID to remove"),
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    output_result(run_client(token, lambda c: c.remove_household_member(household_id, member_id)), fmt)
