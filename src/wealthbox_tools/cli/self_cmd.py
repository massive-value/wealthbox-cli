"""`wbox self ...` — self-management commands.

Module file is ``self_cmd.py`` rather than ``self.py`` because ``self``
is a Python keyword and would shadow it as a module name.

For now this exposes one subcommand:

- ``wbox self upgrade`` — check GitHub for a newer release and, if one is
  available, download, verify, and atomically swap in the new binary
  (Module B tracer; see ``self_upgrade.py`` and issue #32).
"""
from __future__ import annotations

import sys
from pathlib import Path

import typer

from .. import self_upgrade

app = typer.Typer(
    name="self",
    help="Manage the `wbox` CLI itself (upgrade, version checks).",
    no_args_is_help=True,
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _default_install_root() -> Path:
    """Directory containing the running CLI binary.

    For a PyInstaller-bundled ``wbox`` this is the directory of the
    executable itself. For a source / pip install it's the entry-point
    script directory; the swap still works there but the backup file
    lands next to the script — fine for the tracer.
    """
    return Path(sys.executable).resolve().parent


_NON_BUNDLE_UPGRADE_HINTS = {
    "uv-tool": "uv tool upgrade wealthbox-cli",
    "pipx": "pipx upgrade wealthbox-cli",
    "pip": "pip install --upgrade wealthbox-cli",
}


@app.command("upgrade", help="Upgrade the `wbox` CLI to the latest GitHub release.")
def upgrade_cmd() -> None:
    kind = self_upgrade._install_kind()
    if kind != "bundle":
        # The frozen-bundle swap would either silently no-op (uv copies the
        # shim to ~/.local/bin so replacing the venv-side shim doesn't change
        # what PATH resolves) or wedge the venv. Refuse before downloading.
        hint = _NON_BUNDLE_UPGRADE_HINTS.get(kind, _NON_BUNDLE_UPGRADE_HINTS["pip"])
        typer.echo(
            "wbox self upgrade only swaps the standalone binary from "
            "install.ps1.",
            err=True,
        )
        typer.echo(f"This wbox was installed via {kind} — run: {hint}", err=True)
        raise typer.Exit(code=1)

    candidate = self_upgrade.check()
    if candidate is None:
        typer.echo("Already on the latest version.")
        raise typer.Exit(code=0)

    typer.echo(f"Upgrading to v{candidate.version} ({candidate.asset_name})...")
    result = self_upgrade.apply(candidate, install_root=_default_install_root())

    if self_upgrade._is_windows():
        # The rename is deferred to a helper that runs after this process
        # exits, so we cannot honestly claim the upgrade is "installed" yet.
        # The helper writes a status file that next-launch wbox reports.
        typer.echo(
            f"Scheduled v{result.version} — wbox will exit and complete the upgrade."
        )
        typer.echo("Run `wbox --version` after restart to confirm.")
    else:
        typer.echo(f"Installed v{result.version} at {result.installed_path}.")
        typer.echo(f"Previous binary preserved at {result.backup_path}.")
        typer.echo("Restart `wbox` to use the new version.")
