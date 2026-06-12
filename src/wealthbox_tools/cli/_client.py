from __future__ import annotations

import asyncio
import json
import os
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

import typer
from pydantic import ValidationError

from wealthbox_tools.client import WealthboxAPIError, WealthboxClient


def get_client(token: str | None = None) -> WealthboxClient:
    """Create a WealthboxClient with token resolution: --token flag > env var > config file."""
    if token is None:
        token = os.environ.get("WEALTHBOX_TOKEN")
    if token is None:
        from ._config import get_stored_token
        token = get_stored_token()
    if not token:
        raise ValueError(
            "Wealthbox token required. Provide one via any of: "
            "--token flag, WEALTHBOX_TOKEN env var, or `wbox config set-token`."
        )
    return WealthboxClient(token=token)


def run_client(token: str | None, fn: Callable[[WealthboxClient], Awaitable[Any]]) -> Any:
    """Run an async client operation, managing the event loop and client lifecycle."""
    async def _execute() -> Any:
        async with get_client(token) as client:
            return await fn(client)
    return asyncio.run(_execute())


def run_client_with_comments(
    token: str | None,
    fn: Callable[[WealthboxClient], Awaitable[Any]],
    resource_type: str,
    resource_id: int,
    include_comments: bool = True,
) -> Any:
    """Run an async client operation and optionally fetch + merge comments concurrently."""
    async def _with_comments(client: WealthboxClient) -> Any:
        if include_comments:
            result, comments = await asyncio.gather(
                fn(client),
                client.get_comments_for_resource(resource_type, resource_id),
            )
            if isinstance(result, dict):
                result["comments"] = comments
        else:
            result = await fn(client)
        return result
    return run_client(token, _with_comments)


_P = ParamSpec("_P")
_R = TypeVar("_R")


def handle_errors(func: Callable[_P, _R]) -> Callable[_P, _R]:
    @wraps(func)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
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
