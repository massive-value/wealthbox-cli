# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python library providing Pydantic v2 validation models, an async HTTP client (`httpx`), and a CLI (`wbox`) for the Wealthbox CRM API. It validates payloads/queries before they reach the API and is also designed to be used by an OpenClaw agent via Skills + bash.

## Setup

```bash
source venv/Scripts/activate   # activate virtual environment
pip install -e .               # install package with all dependencies
```

Runtime dependencies: `pydantic>=2`, `httpx>=0.27`, `typer>=0.12`, `python-dotenv>=1.0`. Python 3.13+ required.

Auth token goes in `.env` as `WEALTHBOX_TOKEN=<token>`. The client auto-loads it via `python-dotenv`.

## CLI Usage

```bash
wbox --help
wbox me                              # current user info
wbox contacts list --name "Smith"
wbox contacts create '{"first_name": "Jane", "type": "Person"}'
wbox contacts update <id> '{"contact_type": "Client"}'
wbox tasks create '{"title": "Call client", "due_date": "2025-03-15"}'
wbox notes create '{"content": "Note text", "linked_to": [{"id": 123, "type": "Contact"}]}'
```

`create` and `update` commands accept a JSON string. `list` commands accept `--option` flags. Output defaults to JSON; use `--format table` for tabular view.

## Architecture

```
src/wealthbox_tools/
├── models/        # Pydantic validation models (input validation only)
├── client/        # Async httpx client (WealthboxClient)
└── cli/           # Typer CLI app (wbox entry point)
skills/            # OpenClaw SKILL.md files for agent integration
```

### Models (`models/`)

All models exported from `models/__init__.py`. Key base classes in `common.py`:
- `WealthboxModel` — `extra="forbid"`, `populate_by_name=True`
- `RequireAnyFieldModel` — rejects empty payloads; all `*UpdateInput` models use this
- `PaginationQuery` — adds `page`/`per_page`; all `*ListQuery` models inherit this

Enum type aliases in `common.py` (`RecordType`, `ContactType`, `Gender`, `MaritalStatus`, `ContactSource`, `WorkflowStatus`) — used on strict fields. Soft strings kept for account-variable fields (`status`, `visible_to`, kind fields).

**Naming**: `*ListQuery`, `*CreateInput`, `*UpdateInput` per resource. Nested objects (`EmailAddress`, `PhoneNumber`, `StreetAddress`) support `destroy: bool` for Rails-style deletion.

**Custom validators**: `CommentsListQuery` requires ≥1 filter; `OpportunityCreateInput/UpdateInput` requires `pipeline_id`+`stage_id` together; `TaskCreateInput/UpdateInput` requires `assigned_to_user_id` XOR `assigned_to_team_id`; `HouseholdMemberInput` requires `id` or `title`.

### Client (`client/`)

`WealthboxClient` inherits from resource mixins (`ContactsMixin`, `TasksMixin`, etc.) and `_WealthboxBase`. The base handles auth (`ACCESS_TOKEN` header), rate limiting (1 req/sec async token bucket), 429 auto-retry, and error parsing into `WealthboxAPIError`.

```python
async with WealthboxClient() as client:
    contacts = await client.list_contacts(ContactListQuery(name="Smith"))
    note = await client.create_note(NoteCreateInput(content="Hello", linked_to=[LinkedToRef(id=123, type="Contact")]))
```

All methods accept Pydantic model instances and return raw `dict` (API responses are not modeled).

### CLI (`cli/`)

Typer app assembled in `main.py`. Commands: `wbox contacts|tasks|events|opportunities|notes` (CRUD groups) + `wbox me|users|activity|comments|custom-fields` (read-only, registered directly on root). Each command wraps async client calls in `asyncio.run()`.

### OpenClaw Integration (`skills/`)

SKILL.md files teach the agent CLI commands and field references. The agent uses its built-in `bash`/`exec` tools to call `wbox` commands and parse the JSON output.
