"""PyInstaller entry shim for the wbox CLI.

PyInstaller's --onefile mode prefers a script file over a module:function
console-script reference. This shim simply imports the Typer app defined
at ``wealthbox_tools.cli.main:app`` and calls it, so the resulting binary
behaves identically to the ``wbox`` console script registered in
``pyproject.toml``.
"""

from __future__ import annotations

from wealthbox_tools.cli.main import app


def main() -> None:
    app()


if __name__ == "__main__":
    main()
