from __future__ import annotations

import typer

from .activity import app as activity_app
from .categories import app as categories_app
from .contacts import app as contacts_app
from .events import app as events_app
from .households import app as households_app
from .me import app as me_app
from .notes import app as notes_app
from .tasks import app as tasks_app
from .users import app as users_app

app = typer.Typer(
    name="wbox",
    help="Wealthbox CRM CLI — interact with contacts, households, tasks, events, opportunities, and notes.",
    no_args_is_help=True,
)

app.add_typer(activity_app, name="activity")
app.add_typer(categories_app, name="categories")
app.add_typer(contacts_app, name="contacts")
app.add_typer(events_app, name="events")
app.add_typer(households_app, name="households")
app.add_typer(me_app, name="me")
app.add_typer(notes_app, name="notes")
app.add_typer(tasks_app, name="tasks")
app.add_typer(users_app, name="users")


if __name__ == "__main__":
    app()
