# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Wealthbox CLI (`wbox`) is a command-line tool for the Wealthbox CRM API. It provides CRUD access for contacts, tasks, events, and notes, household member management commands, and read/list access for users, activity, `me`, and categories. The API base URL is `https://api.crmworkspace.com/v1`. Official docs: https://dev.wealthbox.com

## Commands

```bash
# Install (editable with dev deps)
pip install -e ".[dev]"

# Run tests
pytest

# Run a single test
pytest tests/path/to/test_file.py::test_name

# Use the CLI (requires WEALTHBOX_TOKEN env var or .env file)
wbox <resource> <command> [options]
```

**Command shape note:** `users` and `activity` use explicit list subcommands (`wbox users list`, `wbox activity list`).

**Activity pagination note:** `/activity` is cursor-based. Use `--cursor` for subsequent pages; do not add `page`/`per_page` parameters for activity queries.

**Authentication:** Set `WEALTHBOX_TOKEN` in `.env` or as an env var. All CLI commands also accept `--token` (hidden option, not shown in `--help`).

## Architecture

Three layers, each in `src/wealthbox_tools/`:

```
cli/        # Typer commands — user-facing, delegates to client
client/     # Async HTTP client built from mixins
models/     # Pydantic v2 models for input validation
```

**Client mixin pattern:** `WealthboxClient` in `client/__init__.py` inherits from all resource mixins (`ActivityMixin`, `CategoriesMixin`, `ContactsMixin`, `EventsMixin`, `HouseholdsMixin`, `MeMixin`, `NotesMixin`, `TasksMixin`, `UsersMixin`) plus `_WealthboxBase` (core HTTP, rate limiting, error handling). To add a new resource, create a mixin and add it to the inheritance chain.

**CLI command pattern:** Each resource module in `cli/` defines a `typer.Typer()` app registered in `cli/main.py`. All commands follow this structure:

```python
@app.command("list")
@handle_errors
def list_contacts(..., fmt: OutputFormat = typer.Option(OutputFormat.JSON, "--format"), token: str | None = typer.Option(None, envvar="WEALTHBOX_TOKEN", hidden=True)):
    result = run_client(token, lambda c: c.list_contacts(query))
    output_result(result, fmt, fields=None if verbose else _DEFAULT_FIELDS)
```

**`add` command pattern:** Create commands are named `add` (not `create`). They take structured flags instead of a raw JSON positional argument. The `contacts add` command also takes a positional record type argument (case-insensitive, validated at the CLI layer). Contacts and tasks expose a `--json` / `--more-fields` escape hatch for complex nested fields.

**`update` command pattern:** Update commands accept only the fields being changed as flags — they do NOT take a JSON positional argument. Build the payload as a dict-comprehension filtering `None`, then pass to the model. Handle `bool | None` fields (e.g. `complete`, `all_day`) explicitly after the comprehension since `False` is a valid value distinct from "not provided":

```python
payload: dict[str, Any] = {k: v for k, v in {
    "name": name,
    "priority": priority,
}.items() if v is not None}
if complete is not None:
    payload["complete"] = complete
linked = build_linked_to(contact, project, opportunity)
if linked is not None:
    payload["linked_to"] = linked
input_model = TaskUpdateInput(**payload)
```

**Authentication:** Token is read from `WEALTHBOX_TOKEN` env var (`.env` auto-loaded via python-dotenv). Passed as `ACCESS_TOKEN` HTTP header. Rate limiting is sliding-window (300 req / 5-min window); state persists across processes via `~/.wbox_rate_limit.json`. 429 responses trigger automatic retry.

**Models:** Input models live in `models/` (e.g., `ContactCreateInput`, `TaskListQuery`). List queries use `exclude_none=True`; update inputs use `exclude_unset=True` to preserve explicit nulls. Enums use Python 3.11+ `StrEnum`. `RequireAnyFieldModel` (in `models/common.py`) rejects empty update payloads. `OutputFormat` (in `cli/_util.py`) is a CLI-layer enum — not a model.

**Output formats:** `output_result` supports `json` (default), `table`, `csv`, `tsv` via the `OutputFormat` enum. Tabular formats flatten nested fields via `_flatten_record` before rendering. `table` uses `tabulate` (simple_grid); `csv`/`tsv` use stdlib `csv`. The total-count footer (`Showing N of M`) goes to stderr so stdout stays pipeable.

**Client-side filtering pattern:** When the API silently ignores a filter param (e.g., `assigned_to` on `/contacts`), add a `list_all_<resource>()` method to the mixin that calls `fetch_all_pages()`, then filter in the CLI layer. Use `err=True` on all progress/warning output so stdout stays clean for piping (applies to all formats, not just JSON).

**Categories:** Category lookups are scoped — resource-specific types via `wbox <resource> categories` (e.g., contact-types, email-types), workspace-level types via `wbox categories` (e.g., tags, opportunity-stages). Resource-scoped category commands are auto-generated by `make_category_command()` in `cli/_util.py`; the `custom-fields` command is hand-written because it needs an extra `--document-type` option.

**Testing:** Uses pytest + respx. Tests are synchronous and use `typer.testing.CliRunner` with `respx.mock` to intercept httpx at the transport layer. The `runner` fixture and `mock_token` autouse fixture live in `tests/conftest.py`. All update tests assert that unset fields are absent from the sent payload (partial-update semantics).

## Adding a New Resource

1. Add Pydantic models to `models/<resource>.py` (CreateInput, UpdateInput, ListQuery)
2. Add a client mixin to `client/<resource>.py` with async CRUD methods; add `list_all_<resource>()` if the resource may need full-dataset fetches (delegates to `fetch_all_pages()`)
3. Register the mixin in `client/__init__.py`
4. Add CLI commands to `cli/<resource>.py` following the command patterns above
5. Register the CLI sub-app in `cli/main.py`
6. If the resource has category types, add them via `make_category_command()` in the resource's `categories` sub-app
7. Add tests in `tests/test_<resource>_create.py` and `tests/test_<resource>_update.py`

## Key Files

- `src/wealthbox_tools/cli/main.py` — registers all sub-apps
- `src/wealthbox_tools/cli/_util.py` — `run_client`, `handle_errors`, `output_result`, `make_category_command`, `build_linked_to`, `active_to_status`, `OutputFormat` (StrEnum: json/table/csv/tsv); tabular helpers: `_flatten_record`, `_extract_collection`, `_render_table`, `_render_kv_table`, `_render_dsv`
- `src/wealthbox_tools/client/base.py` — `_WealthboxBase`, `WealthboxAPIError`, `RateLimiter`
  - `fetch_all_pages(path, params, collection_key, on_progress)` — shared full-dataset paginator; all `list_all_*` methods delegate here
- `src/wealthbox_tools/client/__init__.py` — `WealthboxClient` (combined mixins)
- `src/wealthbox_tools/models/common.py` — base classes: `WealthboxModel`, `RequireAnyFieldModel`, `PaginationQuery`, `LinkedToRef`
- `src/wealthbox_tools/models/enums.py` — all enum definitions
- `tests/conftest.py` — shared `runner` fixture and `mock_token` autouse fixture
