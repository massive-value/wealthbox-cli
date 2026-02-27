from __future__ import annotations

import asyncio
from typing import Optional

import typer

from wealthbox_tools.models import HouseholdMemberInput, HouseholdTitleOptions

from ._util import get_client, handle_errors, output_result

app = typer.Typer(help="Manage household members.", no_args_is_help=True)


@app.command("add-member")
@handle_errors
def add_member(
    household_id: int = typer.Argument(..., help="Household contact ID"),
    member_id: int = typer.Option(..., "--member-id", help="Member contact ID to add"),
    title: HouseholdTitleOptions = typer.Option(..., help="Household title for member (e.g. Spouse, Head)"),
    token: Optional[str] = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format", help="Output format: json or table"),
) -> None:
    """Add a member to a household."""
    payload = HouseholdMemberInput(id=member_id, title=title)

    async def _run() -> dict:
        async with get_client(token) as client:
            return await client.add_household_member(household_id, payload)

    output_result(asyncio.run(_run()), fmt)


@app.command("remove-member")
@handle_errors
def remove_member(
    household_id: int = typer.Argument(..., help="Household contact ID"),
    member_id: int = typer.Argument(..., help="Member contact ID to remove"),
    token: Optional[str] = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: str = typer.Option("json", "--format", help="Output format: json or table"),
) -> None:
    """Remove a member from a household."""

    async def _run() -> dict:
        async with get_client(token) as client:
            return await client.remove_household_member(household_id, member_id)

    output_result(asyncio.run(_run()), fmt)
