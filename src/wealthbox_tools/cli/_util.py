from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

import typer
from pydantic import ValidationError

from wealthbox_tools.client import WealthboxAPIError, WealthboxClient
from wealthbox_tools.models import CategoryListQuery, CategoryType


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
