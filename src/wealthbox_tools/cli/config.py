from __future__ import annotations

import typer

from ._config import _config_path, load_config, save_config

app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Manage wbox CLI configuration.",
    no_args_is_help=True,
)


@app.command(
    "set-token",
    help=(
        "Store your Wealthbox API token. Get one at https://dev.wealthbox.com "
        "(Settings -> API Access -> Access Tokens)."
    ),
)
def set_token(
    token: str | None = typer.Option(
        None, "--token",
        help="API token (will prompt if not provided)",
    ),
) -> None:
    if token is None:
        typer.echo(
            "Find your token at https://dev.wealthbox.com "
            "(Settings -> API Access -> Access Tokens)"
        )
        token = typer.prompt("Wealthbox API token", hide_input=True)
    config = load_config()
    config["token"] = token
    save_config(config)
    typer.echo(f"Token saved to {_config_path()}")


@app.command("show", help="Show current configuration.")
def show() -> None:
    config = load_config()
    if not config:
        typer.echo("No configuration found.")
        typer.echo("Run 'wbox config set-token' to store your API token.")
        return
    token = config.get("token", "")
    masked = f"...{token[-4:]}" if len(token) > 4 else "****"
    typer.echo(f"Token:  {masked}")
    typer.echo(f"Path:   {_config_path()}")


@app.command("clear", help="Remove stored configuration.")
def clear() -> None:
    path = _config_path()
    if path.exists():
        path.unlink()
        typer.echo("Configuration cleared.")
    else:
        typer.echo("No configuration to clear.")
