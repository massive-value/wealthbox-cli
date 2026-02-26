from __future__ import annotations

import typer

from .contacts import app as contacts_app
from .events import app as events_app
from .notes import app as notes_app
from .households import app as households_app
from .readonly import app as readonly_app
from .tasks import app as tasks_app

app = typer.Typer(
    name="wbox",
    help="Wealthbox CRM CLI — interact with contacts, households, tasks, events, opportunities, and notes.",
    no_args_is_help=True,
)

app.add_typer(contacts_app, name="contacts")
app.add_typer(households_app, name="households")
app.add_typer(tasks_app, name="tasks")
app.add_typer(events_app, name="events")
app.add_typer(notes_app, name="notes")

# Read-only top-level commands: wbox me, wbox users, wbox activity, wbox custom-fields
app.add_typer(readonly_app, name="readonly", hidden=True)

# Register read-only commands directly on root for ergonomic access
for cmd in readonly_app.registered_commands:
    app.registered_commands.append(cmd)


if __name__ == "__main__":
    app()
