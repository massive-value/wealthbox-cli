from __future__ import annotations

from typing import Any

import typer

from ._util import (
    OutputFormat,
    _flatten_record,
    _render_kv_table,
    handle_errors,
    output_result,
    run_client,
)

app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Show info about the current authenticated user.",
)


def _relabel_for_table(data: dict[str, Any]) -> dict[str, Any]:
    """Rename top-level `id` to `login_id` and add `user_id (--assigned-to)`
    so the two IDs aren't confusable in tabular output.

    The top-level `id` is a login profile (not usable for `--assigned-to`);
    `current_user.id` is the workspace user ID that filters accept.
    """
    relabeled: dict[str, Any] = {}
    for key, value in data.items():
        relabeled["login_id" if key == "id" else key] = value
    current_user = data.get("current_user")
    if isinstance(current_user, dict) and "id" in current_user:
        relabeled["user_id (--assigned-to)"] = current_user["id"]
    return relabeled


@app.callback(
    invoke_without_command=True,
    help="Show info about the current authenticated user. Use subcommands for more specific info.",
)
@handle_errors
def get_me(
    ctx: typer.Context,
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
    fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"),
) -> None:
    if ctx.invoked_subcommand is not None:
        return
    data = run_client(token, lambda c: c.get_me())
    if fmt == OutputFormat.TABLE and isinstance(data, dict):
        # Bypass output_result's collection-detection heuristic: once we drop
        # the top-level `id` key, it would mistake `users[]` for a collection.
        typer.echo(_render_kv_table(_flatten_record(_relabel_for_table(data))))
        return
    output_result(data, fmt)


@app.command("user-id", help="Print the workspace user ID (for --assigned-to) as a bare integer.")
@handle_errors
def user_id(
    token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True),
) -> None:
    data = run_client(token, lambda c: c.get_me())
    current_user = data.get("current_user") if isinstance(data, dict) else None
    if not isinstance(current_user, dict) or "id" not in current_user:
        raise ValueError("`current_user.id` missing from /me response; cannot determine user ID.")
    typer.echo(current_user["id"])
