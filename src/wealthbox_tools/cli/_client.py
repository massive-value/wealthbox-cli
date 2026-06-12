from __future__ import annotations

import asyncio
import json
import os
import traceback
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

# Exit-code scheme (see README / docs/cli-reference.md):
#   0 — success
#   1 — validation / user error (pydantic ValidationError, 4xx that isn't auth,
#       bad JSON, ValueError, and any other unexpected exception)
#   2 — auth error (WealthboxAPIError 401/403). NOTE: Click/Typer also uses 2
#       for usage errors (bad/missing CLI args), which are raised by the parser
#       BEFORE handle_errors runs. That overlap is pre-existing and acceptable.
#   3 — server error (WealthboxAPIError >= 500)
_EXIT_VALIDATION = 1
_EXIT_AUTH = 2
_EXIT_SERVER = 3


def _exit_code_for_api_error(status_code: int) -> int:
    """Map a WealthboxAPIError HTTP status to a differentiated exit code."""
    if status_code in (401, 403):
        return _EXIT_AUTH
    if status_code >= 500:
        return _EXIT_SERVER
    # All other statuses (4xx that isn't auth, plus the synthetic 0 used for
    # transport-level failures) are treated as user/validation errors.
    return _EXIT_VALIDATION


def _debug_enabled() -> bool:
    """True when WBOX_DEBUG is set to any non-empty value.

    Matches the repo's existing env-flag idiom (see WBOX_BRIEF in cli/_format.py):
    any non-empty value is truthy.
    """
    return bool(os.environ.get("WBOX_DEBUG"))


def handle_errors(func: Callable[_P, _R]) -> Callable[_P, _R]:
    @wraps(func)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        try:
            return func(*args, **kwargs)

        except WealthboxAPIError as e:
            typer.echo(f"API Error ({e.status_code}): {e.detail}", err=True)
            if _debug_enabled():
                typer.echo(traceback.format_exc(), err=True)
            raise typer.Exit(code=_exit_code_for_api_error(e.status_code))

        except ValidationError as e:
            typer.echo("Validation Error:", err=True)
            for err_item in e.errors():
                loc = " -> ".join(str(x) for x in err_item["loc"])
                msg = err_item["msg"]
                typer.echo(f"  {loc}: {msg}", err=True)
            if _debug_enabled():
                typer.echo(traceback.format_exc(), err=True)
            raise typer.Exit(code=_EXIT_VALIDATION)

        except json.JSONDecodeError as e:
            typer.echo(f"Invalid JSON: {e}", err=True)
            if _debug_enabled():
                typer.echo(traceback.format_exc(), err=True)
            raise typer.Exit(code=_EXIT_VALIDATION)

        except ValueError as e:
            typer.echo(f"Error: {e}", err=True)
            if _debug_enabled():
                typer.echo(traceback.format_exc(), err=True)
            raise typer.Exit(code=_EXIT_VALIDATION)

        except Exception as e:
            typer.echo(f"Unexpected error: {e}", err=True)
            if _debug_enabled():
                typer.echo(traceback.format_exc(), err=True)
            raise typer.Exit(code=_EXIT_VALIDATION)

    return wrapper
