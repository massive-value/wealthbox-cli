from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

import typer
from pydantic import ValidationError

from wealthbox_tools.client import WealthboxAPIError, WealthboxClient
from wealthbox_tools.models import CategoryListQuery, CategoryType, LinkedToRef, TaskResourceType


def get_client(token: str | None = None) -> WealthboxClient:
    """Create a WealthboxClient, auto-loading .env if python-dotenv is available."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    return WealthboxClient(token=token)


def run_client(token: str | None, fn: Callable[[WealthboxClient], Awaitable[Any]]) -> Any:
    """Run an async client operation, managing the event loop and client lifecycle."""
    async def _execute() -> Any:
        async with get_client(token) as client:
            return await fn(client)
    return asyncio.run(_execute())


_SUPPORTED_FORMATS = ("json",)


def _filter_fields(data: Any, fields: list[str]) -> Any:
    if isinstance(data, list):
        return [{f: item[f] for f in fields if f in item} for item in data]
    if isinstance(data, dict):
        if "meta" in data:
            return {
                k: ([{f: item[f] for f in fields if f in item} for item in v] if isinstance(v, list) else v)
                for k, v in data.items()
            }
        return {f: data[f] for f in fields if f in data}
    return data


def truncate_nested_field(data: Any, parent: str, fields: list[str], max_len: int) -> Any:
    """Truncate one or more string fields nested inside a dict field in each item of a response."""
    def _trim(item: Any) -> Any:
        if not (isinstance(item, dict) and isinstance(item.get(parent), dict)):
            return item
        nested = item[parent]
        updates = {
            f: nested[f][:max_len] + "..."
            for f in fields
            if f in nested and isinstance(nested[f], str) and len(nested[f]) > max_len
        }
        if updates:
            item = {**item, parent: {**nested, **updates}}
        return item

    if isinstance(data, list):
        return [_trim(item) for item in data]
    if isinstance(data, dict):
        return {k: [_trim(i) for i in v] if isinstance(v, list) else v for k, v in data.items()}
    return _trim(data)


def truncate_field(data: Any, field: str, max_len: int) -> Any:
    """Truncate a string field in each item of a response to max_len characters."""
    def _trim(item: Any) -> Any:
        if isinstance(item, dict) and field in item and isinstance(item[field], str):
            if len(item[field]) > max_len:
                item = {**item, field: item[field][:max_len] + "..."}
        return item

    if isinstance(data, list):
        return [_trim(item) for item in data]
    if isinstance(data, dict):
        return {k: [_trim(i) for i in v] if isinstance(v, list) else v for k, v in data.items()}
    return _trim(data)


def output_result(data: Any, fmt: str = "json", fields: list[str] | None = None) -> None:
    """Print result to stdout in the requested format."""
    if fmt not in _SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format '{fmt}'. Supported formats: {', '.join(_SUPPORTED_FORMATS)}")
    if fields is not None:
        data = _filter_fields(data, fields)
    typer.echo(json.dumps(data, indent=2, default=str))


def handle_errors(func):  # type: ignore[no-untyped-def]
    @wraps(func)
    def wrapper(*args, **kwargs):  # type: ignore[no-untyped-def]
        try:
            return func(*args, **kwargs)

        except WealthboxAPIError as e:
            typer.echo(f"API Error ({e.status_code}): {e.detail}", err=True)
            raise typer.Exit(code=1)

        except ValidationError as e:
            typer.echo("Validation Error:", err=True)
            for err_item in e.errors():
                loc = " -> ".join(str(x) for x in err_item["loc"])
                msg = err_item["msg"]
                typer.echo(f"  {loc}: {msg}", err=True)
            raise typer.Exit(code=1)

        except json.JSONDecodeError as e:
            typer.echo(f"Invalid JSON: {e}", err=True)
            raise typer.Exit(code=1)

        except ValueError as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(code=1)

        except Exception as e:
            typer.echo(f"Unexpected error: {e}", err=True)
            raise typer.Exit(code=1)

    return wrapper


def active_to_status(active: bool | None) -> str | None:
    """Map --active/--inactive flag to Wealthbox status string."""
    if active is True:
        return "Active"
    if active is False:
        return "Inactive"
    return None


def build_linked_to(
    contact: int | None,
    project: int | None,
    opportunity: int | None,
) -> list[LinkedToRef] | None:
    """Build a linked_to list from typed ID options. Returns None if none provided."""
    refs: list[LinkedToRef] = []
    if contact is not None:
        refs.append(LinkedToRef(id=contact, type="Contact"))
    if project is not None:
        refs.append(LinkedToRef(id=project, type="Project"))
    if opportunity is not None:
        refs.append(LinkedToRef(id=opportunity, type="Opportunity"))
    return refs if refs else None


def build_resource_filter(
    contact: int | None,
    project: int | None,
    opportunity: int | None,
) -> tuple[int | None, TaskResourceType | None]:
    """Map friendly --contact/--project/--opportunity options to (resource_id, resource_type).

    Raises BadParameter if more than one is provided.
    Returns (None, None) if none are provided.
    """
    result: tuple[int | None, TaskResourceType | None] = (None, None)
    for id_, rtype in ((contact, TaskResourceType.CONTACT), (project, TaskResourceType.PROJECT), (opportunity, TaskResourceType.OPPORTUNITY)):
        if id_ is not None:
            if result[0] is not None:
                raise typer.BadParameter("Provide only one of --contact, --project, or --opportunity.")
            result = (id_, rtype)
    return result


def make_category_command(category_type: CategoryType):  # type: ignore[no-untyped-def]
    """Factory that returns a Typer command function for listing a category type."""
    @handle_errors
    def cmd(
        page: int | None = typer.Option(None, help="Page number"),
        per_page: int | None = typer.Option(None, "--per-page", help="Results per page (max 100)"),
        token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
        fmt: str = typer.Option("json", "--format"),
    ) -> None:
        query = CategoryListQuery(page=page, per_page=per_page)
        output_result(run_client(token, lambda c: c.list_categories(category_type, query)), fmt)
    return cmd
