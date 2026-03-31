from __future__ import annotations

from importlib.metadata import version as _pkg_version

import typer

from .activity import app as activity_app
from .categories import app as categories_app
from .comments import app as comments_app
from .contacts import app as contacts_app
from .events import app as events_app
from .households import app as households_app
from .me import app as me_app
from .notes import app as notes_app
from .opportunities import app as opportunities_app
from .projects import app as projects_app
from .tasks import app as tasks_app
from .users import app as users_app
from .workflows import app as workflows_app

app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]}, 
    name="wbox",
    help="Wealthbox CRM CLI — interact with contacts, households, tasks, events, opportunities, and notes.",
    no_args_is_help=True,
)

@app.callback(invoke_without_command=True)
def _main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", is_eager=True, help="Show version and exit."),
) -> None:
    if version:
        typer.echo(_pkg_version("wealthbox-cli"))
        raise typer.Exit()


app.add_typer(activity_app, name="activity")
app.add_typer(categories_app, name="categories")
app.add_typer(comments_app, name="comments")
app.add_typer(contacts_app, name="contacts")
app.add_typer(events_app, name="events")
app.add_typer(households_app, name="households")
app.add_typer(me_app, name="me")
app.add_typer(notes_app, name="notes")
app.add_typer(opportunities_app, name="opportunities")
app.add_typer(projects_app, name="projects")
app.add_typer(tasks_app, name="tasks")
app.add_typer(users_app, name="users")
app.add_typer(workflows_app, name="workflows")


if __name__ == "__main__":
    app()
