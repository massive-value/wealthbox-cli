# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`wealthbox-tools` is a Python CLI and async HTTP client library for the [Wealthbox CRM API](https://dev.wealthbox.com). The CLI entry point is `wbox`.

## Commands

```bash
# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run the CLI
wbox --help
wbox contacts list
wbox tasks list
wbox me

# Run tests
pytest

# Run a single test file
pytest tests/path/to/test_file.py

# Run a single test
pytest tests/path/to/test_file.py::test_name
```

**Authentication**: Set `WEALTHBOX_TOKEN` in a `.env` file or as an env var. All CLI commands also accept `--token`.

## Architecture

The project has three layers under `src/wealthbox_tools/`:

### `models/`
Pydantic v2 models for request validation and API typing:
- `common.py` — Base classes (`WealthboxModel` with `extra="forbid"`, `RequireAnyFieldModel`, `PaginationQuery`), shared nested types (EmailAddress, PhoneNumber, etc.)
- `enums.py` — Wealthbox API Literal types (RecordTypeOptions, TaskFrameOptions, CategoryTypeOptions, DocumentTypeOptions, etc.). Only contains types fixed by the Wealthbox API; workspace-customizable fields (contact types, sources, email/phone/address kinds) use plain `str`.
- Per-resource files (`contacts.py`, `tasks.py`, `events.py`, `notes.py`, `households.py`) — Create/Update inputs and list query models

### `client/`
Async HTTP client using `httpx.AsyncClient`:
- `base.py` — `_WealthboxBase`: connection to `https://api.crmworkspace.com/v1`, `ACCESS_TOKEN` header auth, token-bucket rate limiting (1 req/sec), 429 retry logic, `WealthboxAPIError`
- Per-resource mixins (`contacts.py`, `tasks.py`, etc.) — CRUD methods per resource
- `__init__.py` — `WealthboxClient` composes all mixins: `ContactsMixin + TasksMixin + EventsMixin + NotesMixin + HouseholdsMixin + ReadOnlyMixin + _WealthboxBase`

Usage pattern:
```python
async with WealthboxClient(token="...") as client:
    result = await client.list_contacts(query)
```

### `cli/`
Typer-based CLI with one module per resource:
- `main.py` — Root app; registers sub-apps (`contacts`, `tasks`, `events`, `notes`, `households`, `categories`) and readonly commands (`me`, `users`, `activity`) at the root level
- `_util.py` — `get_client()` (loads .env, creates client), `output_result()` (JSON formatting), `@handle_errors` decorator, `make_category_command()` factory for category listing commands
- `categories.py` — Top-level `wbox categories` sub-app for workspace-level categories (tags, custom-fields, opportunity stages, etc.)

CLI command pattern:
```python
@app.command("list")
@handle_errors
def list_contacts(..., token: Optional[str] = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True)):
    async def _run():
        async with get_client(token) as client:
            return await client.list_contacts(query)
    output_result(asyncio.run(_run()), fmt)
```

## Categories

Category lookups are scoped to the resource they belong to:
- **Contact categories** → `wbox contacts categories <type>` (contact-types, contact-sources, email-types, phone-types, address-types, website-types, contact-roles)
- **Task categories** → `wbox tasks categories`
- **Event categories** → `wbox events categories`
- **Workspace-level** → `wbox categories <type>` (tags, custom-fields, file-categories, opportunity-stages, opportunity-pipelines, investment-objectives, financial-account-types)

Resource-scoped category commands are registered via `make_category_command()` from `_util.py`. The only hand-written category command is `custom-fields` (it has an extra `--document-type` option).

## Adding a New Resource

1. Add Pydantic models to `models/<resource>.py` (CreateInput, UpdateInput, ListQuery)
2. Add a client mixin to `client/<resource>.py` with async CRUD methods
3. Register the mixin in `client/__init__.py`
4. Add CLI commands to `cli/<resource>.py` following the existing pattern
5. Register the CLI sub-app in `cli/main.py`
6. If the resource has Wealthbox category types, add them via `make_category_command()` — either as a `categories` sub-app (multiple types) or a single `categories` command

## Testing

Uses pytest + pytest-asyncio + respx (HTTP mocking). Tests are async and mock the httpx transport layer via `respx.mock`.
