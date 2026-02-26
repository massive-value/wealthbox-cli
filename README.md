# wealthbox-tools

A Python library for interacting with the [Wealthbox CRM API](https://dev.wealthbox.com). Includes:

- **Pydantic v2 validation models** — catch bad payloads before they hit the API
- **Async HTTP client** — `WealthboxClient` backed by `httpx`
- **CLI** — `wbox` command for direct terminal interaction
- **OpenClaw Skills** — SKILL.md files for agent-driven automation via bash

---

## Requirements

- Python 3.13+
- A Wealthbox API token (from your [Wealthbox settings](https://app.crmworkspace.com/settings/api))

---

## Installation

```bash
git clone <repo-url>
cd wealthbox-tools

# Create and activate virtual environment
python -m venv venv
source venv/Scripts/activate    # Windows (Git Bash / WSL)
# source venv/bin/activate       # macOS / Linux

pip install -e .
```

### Authentication

Create a `.env` file in the project root:

```
WEALTHBOX_TOKEN=your_token_here
```

The client and CLI both auto-load this file via `python-dotenv`. You can also pass the token explicitly:

```bash
wbox --token your_token_here me
# or
export WEALTHBOX_TOKEN=your_token_here
```

---

## CLI Quick Start

```bash
# Verify your token
wbox me

# List contacts
wbox contacts list
wbox contacts list --name "Smith" --contact-type "Client" --per-page 25

# Get a single contact
wbox contacts get 12345

# Create a contact (fields as JSON)
wbox contacts create '{"first_name": "Jane", "last_name": "Doe", "type": "Person", "contact_type": "Prospect"}'

# Update a contact
wbox contacts update 12345 '{"contact_type": "Client", "status": "Active"}'

# Create a task
wbox tasks create '{"title": "Follow up call", "due_date": "2025-03-20", "frame": "specific"}'

# Create a note linked to a contact
wbox notes create '{"content": "Discussed Q1 review.", "linked_to": [{"id": 12345, "type": "Contact"}]}'
```

Output defaults to JSON. Use `--format table` for tabular output on list commands.

See [`src/wealthbox_tools/cli/README.md`](src/wealthbox_tools/cli/README.md) for the full CLI reference.

---

## Python Client

```python
import asyncio
from wealthbox_tools import WealthboxClient
from wealthbox_tools.models import ContactCreateInput, ContactListQuery, NoteCreateInput, LinkedToRef

async def main():
    async with WealthboxClient() as client:
        # Get current user
        me = await client.get_me()
        print(me["name"])

        # List contacts
        result = await client.list_contacts(ContactListQuery(name="Smith", per_page=10))
        for contact in result["contacts"]:
            print(contact["id"], contact.get("name"))

        # Create a contact
        new_contact = await client.create_contact(
            ContactCreateInput(
                first_name="Jane",
                last_name="Doe",
                type="Person",
                contact_type="Prospect",
            )
        )
        contact_id = new_contact["id"]

        # Create a note linked to the contact
        await client.create_note(
            NoteCreateInput(
                content="Initial intake call completed.",
                linked_to=[LinkedToRef(id=contact_id, type="Contact")],
            )
        )

asyncio.run(main())
```

### Client Methods

| Method | Description |
|--------|-------------|
| `get_me()` | Current authenticated user |
| `list_users(page, per_page)` | All account users |
| `list_contacts(query)` | Filter/paginate contacts |
| `get_contact(id)` | Single contact |
| `create_contact(data)` | Create contact |
| `update_contact(id, data)` | Update contact |
| `delete_contact(id)` | Delete contact |
| `list_tasks(query)` | Filter/paginate tasks |
| `get_task(id)` | Single task |
| `create_task(data)` | Create task |
| `update_task(id, data)` | Update task |
| `delete_task(id)` | Delete task |
| `list_events(query)` | Filter/paginate events |
| `get_event(id)` | Single event |
| `create_event(data)` | Create event |
| `update_event(id, data)` | Update event |
| `delete_event(id)` | Delete event |
| `list_opportunities(query)` | Filter/paginate opportunities |
| `get_opportunity(id)` | Single opportunity |
| `create_opportunity(data)` | Create opportunity |
| `update_opportunity(id, data)` | Update opportunity |
| `delete_opportunity(id)` | Delete opportunity |
| `list_notes(query)` | Filter/paginate notes |
| `get_note(id)` | Single note |
| `create_note(data)` | Create note |
| `update_note(id, data)` | Update note |
| `list_activity(query)` | Activity feed |
| `list_comments(query)` | Comments on records |
| `list_custom_fields(query)` | Custom field definitions |
| `add_household_member(household_id, payload)` | Add a member to a household |
| `remove_household_member(household_id, member_id)` | Remove a member from a household |

All methods return raw `dict` from the API response. All `create_*` and `update_*` methods accept Pydantic model instances — validation runs before the HTTP call.

---

## Validation Models

Models live in `src/wealthbox_tools/models/`. All inherit from `WealthboxModel` which enforces `extra="forbid"` (rejects unknown fields).

### Input Models

```python
from wealthbox_tools.models import (
    ContactCreateInput, ContactUpdateInput, ContactListQuery,
    TaskCreateInput, TaskUpdateInput, TaskListQuery,
    EventCreateInput, EventUpdateInput, EventListQuery,
    OpportunityCreateInput, OpportunityUpdateInput, OpportunityListQuery,
    NoteCreateInput, NoteUpdateInput, NoteListQuery,
)
```

**`*CreateInput`** — payload for POST. Some fields are required (e.g., `EventCreateInput.title`, `TaskCreateInput.due_date`).

**`*UpdateInput`** — payload for PUT/PATCH. Rejects completely empty payloads (at least one field required). Allows explicit `None` for clearing fields.

**`*ListQuery`** — query parameters for list endpoints. All fields optional; paginated via `page` / `per_page`.

### Enum Types

These fields are constrained to known Wealthbox values:

| Type Alias | Field | Allowed Values |
|------------|-------|----------------|
| `RecordType` | `contact.type` | `Person`, `Household`, `Organization`, `Trust` |
| `ContactType` | `contact.contact_type` | `Client`, `Prospect`, `Lead`, `401(k) Participant`, `Center of Influence`, `Flourish Only`, `External (Non-Client)` |
| `Gender` | `contact.gender` | `Female`, `Male`, `Non-binary`, `Unknown` |
| `MaritalStatus` | `contact.marital_status` | `Married`, `Single`, `Divorced`, `Widowed`, `Life Partner`, `Separated`, `Unknown` |
| `ContactSource` | `contact.contact_source` | `Client Referral`, `Squire Referral`, `Friend/Family of Advisor`, `COI Referral`, `Conference`, `Call In`, `Website`, `Other Digital Media`, `Events/Seminars`, `Merger/Acquisition`, `Lead Gen Service`, `Person or Spouse is an Employee` |
| `WorkflowStatus` | `workflow.status` | `active`, `completed`, `scheduled` |
| `TaskFrame` | `task.frame` | `today`, `tomorrow`, `this_week`, `next_week`, `future`, `specific` |

> **Note:** `contact.contact_type` (ContactType) are account-defined values. If your account uses non-standard classifications, widen this field to `str` in `models/contacts.py`.

Fields kept as soft strings (account-variable): `status`, `visible_to`, `EmailAddress.kind`, `PhoneNumber.kind`, `StreetAddress.kind`.

### Nested Objects

`EmailAddress`, `PhoneNumber`, and `StreetAddress` support Rails-style nested attribute deletion:

```python
# Delete a specific email address (provide its ID from a GET first)
ContactUpdateInput(
    email_addresses=[EmailAddress(id=999, destroy=True)]
)
```

### Cross-field Validators

| Model | Rule |
|-------|------|
| `CommentsListQuery` | At least one filter field required (not just pagination) |
| `OpportunityCreateInput` / `OpportunityUpdateInput` | `pipeline_id` and `stage_id` must both be set or both be absent |
| `TaskCreateInput` / `TaskUpdateInput` | `assigned_to_user_id` and `assigned_to_team_id` are mutually exclusive |
| `HouseholdMemberInput` | Requires either `id` or `title` |

---

## Project Structure

```
wealthbox-tools/
├── .env                         # WEALTHBOX_TOKEN (not committed)
├── pyproject.toml               # Package config, dependencies, wbox entry point
├── src/wealthbox_tools/
│   ├── __init__.py              # Top-level exports (client + models)
│   ├── models/                  # Pydantic validation models
│   │   ├── common.py            # Base classes + enum type aliases
│   │   ├── contacts.py
│   │   ├── tasks.py
│   │   ├── events.py
│   │   ├── opportunities.py
│   │   ├── notes.py
│   │   ├── workflows.py
│   │   ├── activity.py
│   │   ├── comments.py
│   │   ├── households.py
│   │   ├── metadata.py
│   │   └── projects.py
│   ├── client/                  # Async httpx API client
│   │   ├── base.py              # WealthboxClient core, RateLimiter, WealthboxAPIError
│   │   ├── contacts.py          # ContactsMixin
│   │   ├── tasks.py             # TasksMixin
│   │   ├── events.py            # EventsMixin
│   │   ├── opportunities.py     # OpportunitiesMixin
│   │   ├── notes.py             # NotesMixin
│   │   └── readonly.py          # ReadOnlyMixin (me, users, activity, comments, custom_fields)
│   └── cli/                     # Typer CLI (wbox command)
│       ├── main.py              # Root app, command group assembly
│       ├── _util.py             # Shared helpers (get_client, output_result, handle_errors)
│       ├── contacts.py
│       ├── tasks.py
│       ├── events.py
│       ├── opportunities.py
│       ├── notes.py
│       └── readonly.py
└── skills/                      # OpenClaw SKILL.md files
    ├── SKILL-contacts.md
    ├── SKILL-tasks.md
    ├── SKILL-events.md
    ├── SKILL-opportunities.md
    ├── SKILL-notes.md
    └── SKILL-readonly.md
```

---

## OpenClaw Agent Integration

The `skills/` directory contains SKILL.md files for [OpenClaw](https://github.com/openclaw/openclaw) agent integration. The agent uses its built-in `bash`/`exec` tools to run `wbox` commands and processes the JSON output.

Place the skill files where your OpenClaw workspace discovers them (typically `${workspaceDir}/skills/`) or reference the `skills/` directory in your OpenClaw config.

---

## API Reference

- Base URL: `https://api.crmworkspace.com/v1`
- Auth: `ACCESS_TOKEN` header
- Rate limit: 1 req/sec sustained; returns `429` on excess (auto-retried by client)
- Pagination: `page` + `per_page` params; response includes `meta.total_count` / `meta.total_pages`

Full API docs: [dev.wealthbox.com](https://dev.wealthbox.com)
