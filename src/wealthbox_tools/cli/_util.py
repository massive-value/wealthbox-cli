from __future__ import annotations

import asyncio
import functools
import json
import sys
from typing import Any, Optional

import typer

from wealthbox_tools.client import WealthboxAPIError, WealthboxClient


def get_client(token: str | None = None) -> WealthboxClient:
    """Create a WealthboxClient, auto-loading .env if python-dotenv is available."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    return WealthboxClient(token=token)


def output_result(data: Any, fmt: str = "json") -> None:
    """Print result to stdout in the requested format."""
    typer.echo(json.dumps(data, indent=2, default=str))



def handle_errors(func):  # type: ignore[no-untyped-def]
    """Decorator that catches known exceptions and prints user-friendly errors."""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except json.JSONDecodeError as e:
            typer.echo(f"Invalid JSON: {e}", err=True)
            raise typer.Exit(code=1)
        except ValueError as e:
            typer.echo(f"Validation error: {e}", err=True)
            raise typer.Exit(code=1)
        except WealthboxAPIError as e:
            typer.echo(f"API error {e.status_code}: {e.detail}", err=True)
            raise typer.Exit(code=1)
        except Exception as e:
            typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(code=1)
    return wrapper


def make_category_command(category_type: str):  # type: ignore[no-untyped-def]
    """Factory that returns a Typer command function for listing a category type."""
    @handle_errors
    def cmd(
        token: Optional[str] = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
        fmt: str = typer.Option("json", "--format"),
    ) -> None:
        async def _run() -> dict:
            async with get_client(token) as client:
                return await client.list_custom_categories(category_type)
        output_result(asyncio.run(_run()), fmt)
    return cmd
