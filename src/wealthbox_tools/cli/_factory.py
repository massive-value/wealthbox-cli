from __future__ import annotations

from collections.abc import Callable

import click
import typer
from typer.core import TyperGroup

from wealthbox_tools.models import CategoryListQuery, CategoryType

from ._client import handle_errors, run_client
from ._format import OutputFormat, output_result


class _GetShortcutGroup(TyperGroup):
    """Typer Group that routes numeric first arguments to the ``get`` subcommand."""

    def resolve_command(
        self, ctx: click.Context, args: list[str]
    ) -> tuple[str | None, click.Command | None, list[str]]:
        if args and args[0].isdigit() and args[0] not in self.commands:
            args.insert(0, "get")
        return super().resolve_command(ctx, args)


def make_resource_app(*, help: str) -> typer.Typer:
    """Create a Typer app that supports ``wbox <resource> <id>`` as shorthand for ``get <id>``."""
    return typer.Typer(
        cls=_GetShortcutGroup,
        context_settings={"help_option_names": ["-h", "--help"]},
        help=help,
        no_args_is_help=True,
    )


# Maps CLI resource names to the CommentResourceType string expected by GET /comments
COMMENT_RESOURCE_TYPES: dict[str, str] = {
    "tasks": "Task",
    "events": "Event",
    "notes": "StatusUpdates",
    "opportunities": "Opportunity",
    "projects": "Project",
    "workflows": "Workflow",
}


def make_category_command(category_type: CategoryType) -> Callable[..., None]:
    """Factory that returns a Typer command function for listing a category type."""
    @handle_errors
    def cmd(
        page: int | None = typer.Option(None, help="Page number"),
        per_page: int | None = typer.Option(None, "--per-page", help="Results per page (max 100)"),
        token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
        fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
    ) -> None:
        query = CategoryListQuery(page=page, per_page=per_page)
        output_result(run_client(token, lambda c: c.list_categories(category_type, query)), fmt)
    return cmd
