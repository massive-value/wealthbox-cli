from __future__ import annotations

import json

import typer

from ._skill_platforms import detect_platforms, is_installed, skill_dir

app = typer.Typer(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Install and manage the wealthbox-crm agent skill.",
    no_args_is_help=True,
)


@app.command("list", help="Show where the skill is installed per platform.")
def list_platforms() -> None:
    header = ("platform", "path", "status", "last-bootstrap")
    rows: list[tuple[str, str, str, str]] = []
    for p in detect_platforms():
        dest = skill_dir(p)
        installed = is_installed(p)
        meta_file = dest / "firm" / "_meta.json"
        last_bootstrap = "—"
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text())
                files = meta.get("files", {})
                if files:
                    last_bootstrap = max(files.values())
            except (json.JSONDecodeError, OSError):
                last_bootstrap = "(unreadable)"
        rows.append((
            p.id,
            str(dest),
            "installed" if installed else "not installed",
            last_bootstrap,
        ))

    widths = [
        max(len(r[i]) for r in ([header] + rows))
        for i in range(4)
    ]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    typer.echo(fmt.format(*header))
    typer.echo(fmt.format(*("-" * w for w in widths)))
    for r in rows:
        typer.echo(fmt.format(*r))
