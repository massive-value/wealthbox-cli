from __future__ import annotations

import asyncio
import csv
import io
import json
from collections.abc import Awaitable, Callable
from enum import StrEnum
from functools import wraps
from typing import Any

import typer
from pydantic import ValidationError

from wealthbox_tools.client import WealthboxAPIError, WealthboxClient
from wealthbox_tools.models import CategoryListQuery, CategoryType, LinkedToRef, TaskResourceType


def get_client(token: str | None = None) -> WealthboxClient:
    """Create a WealthboxClient with token resolution: --token flag > env var > config file > .env."""
    import os
    if token is None:
        token = os.environ.get("WEALTHBOX_TOKEN")
    if token is None:
        from ._config import get_stored_token
        token = get_stored_token()
    if token is None:
        try:
            from dotenv import load_dotenv
            load_dotenv()
            token = os.environ.get("WEALTHBOX_TOKEN")
        except ImportError:
            pass
    return WealthboxClient(token=token)


def run_client(token: str | None, fn: Callable[[WealthboxClient], Awaitable[Any]]) -> Any:
    """Run an async client operation, managing the event loop and client lifecycle."""
    async def _execute() -> Any:
        async with get_client(token) as client:
            return await fn(client)
    return asyncio.run(_execute())


class OutputFormat(StrEnum):
    JSON = "json"
    TABLE = "table"
    CSV = "csv"
    TSV = "tsv"


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


def _flatten_value(value: Any) -> Any:
    """Convert a single field value to a scalar suitable for tabular display."""
    if value is None:
        return ""
    if isinstance(value, list):
        if not value:
            return ""
        first = value[0]
        if isinstance(first, str):
            # e.g. tags: ["VIP", "Prospect"]
            return ", ".join(str(v) for v in value)
        if isinstance(first, dict):
            if "address" in first:
                # e.g. email_addresses, phone_numbers — return principal's address
                for item in value:
                    if item.get("principal"):
                        return item["address"]
                return first["address"]
            if "id" in first and "type" in first:
                # e.g. linked_to, invitees
                return f"{first['type']}:{first['id']}"
            return f"[{len(value)} items]"
    if isinstance(value, dict):
        return json.dumps(value)
    return value


def _flatten_record(record: dict) -> dict:  # type: ignore[type-arg]
    return {k: _flatten_value(v) for k, v in record.items()}


def _extract_collection(data: Any) -> tuple[list[dict] | None, int | None]:  # type: ignore[type-arg]
    """Return (rows, total_count) or (None, None) for a single-object response."""
    if isinstance(data, list):
        return data, None
    if isinstance(data, dict):
        if "meta" in data:
            rows: list[dict] = []  # type: ignore[type-arg]
            for k, v in data.items():
                if k != "meta" and isinstance(v, list):
                    rows = v
                    break
            total = data["meta"].get("total_count") or data["meta"].get("total_entries")
            return rows, total
        # Check if any value is a list (collection without meta)
        for v in data.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return v, None
    return None, None


def _render_table(rows: list[dict], headers: list[str], total_count: int | None) -> tuple[str, str | None]:  # type: ignore[type-arg]
    from tabulate import tabulate
    table_data = [[row.get(h, "") for h in headers] for row in rows]
    rendered = tabulate(table_data, headers=headers, tablefmt="simple_grid")
    footer = f"Showing {len(rows)} of {total_count} results" if total_count is not None else None
    return rendered, footer


def _render_kv_table(record: dict) -> str:  # type: ignore[type-arg]
    from tabulate import tabulate
    return tabulate(list(record.items()), headers=["Field", "Value"], tablefmt="simple_grid")


def _render_dsv(rows: list[dict], headers: list[str], sep: str) -> str:  # type: ignore[type-arg]
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=sep)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([row.get(h, "") for h in headers])
    return buf.getvalue()


def output_result(data: Any, fmt: OutputFormat = OutputFormat.JSON, fields: list[str] | None = None) -> None:
    """Print result to stdout in the requested format."""
    if fields is not None:
        data = _filter_fields(data, fields)
    if fmt == OutputFormat.JSON:
        typer.echo(json.dumps(data, indent=2, default=str))
        return

    # Tabular formats
    sep = "\t" if fmt == OutputFormat.TSV else ","
    rows, total_count = _extract_collection(data)
    if rows is None:
        # Single object
        record = _flatten_record(data if isinstance(data, dict) else {"value": data})
        if fmt == OutputFormat.TABLE:
            typer.echo(_render_kv_table(record))
        else:
            typer.echo(_render_dsv([record], list(record.keys()), sep), nl=False)
    else:
        flat_rows = [_flatten_record(r) for r in rows]
        headers = list(flat_rows[0].keys()) if flat_rows else []
        if fmt == OutputFormat.TABLE:
            rendered, footer = _render_table(flat_rows, headers, total_count)
            typer.echo(rendered)
            if footer:
                typer.echo(footer, err=True)
        else:
            typer.echo(_render_dsv(flat_rows, headers, sep), nl=False)


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
    for id_, rtype in (
        (contact, TaskResourceType.CONTACT),
        (project, TaskResourceType.PROJECT),
        (opportunity, TaskResourceType.OPPORTUNITY),
    ):
        if id_ is not None:
            if result[0] is not None:
                raise typer.BadParameter("Provide only one of --contact, --project, or --opportunity.")
            result = (id_, rtype)
    return result


def parse_more_fields(more_fields: str, reserved: set[str]) -> dict[str, Any]:
    """Parse --more-fields JSON and validate against reserved keys.

    Raises BadParameter if the value is not valid JSON, not an object, or collides with
    a reserved key that has an explicit CLI flag.
    """
    try:
        extra = json.loads(more_fields)
    except json.JSONDecodeError as e:
        raise typer.BadParameter(f"--more-fields must be valid JSON: {e.msg}") from e
    if not isinstance(extra, dict):
        raise typer.BadParameter("--more-fields must be a JSON object (e.g. {...}), not a list or string.")
    collision = reserved.intersection(extra.keys())
    if collision:
        raise typer.BadParameter(f"--more-fields cannot include {sorted(collision)}; use explicit CLI args instead.")
    return extra


def make_category_command(category_type: CategoryType):  # type: ignore[no-untyped-def]
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
