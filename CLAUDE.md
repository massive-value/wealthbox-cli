# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Wealthbox CLI (`wbox`) is a command-line tool for the Wealthbox CRM API. It provides CRUD access for contacts, tasks, events, and notes, household member management commands, and read/list access for users, activity, `me`, and categories. The API base URL is `https://api.crmworkspace.com/v1`. Official docs: https://dev.wealthbox.com

## Package

Published to PyPI as `wealthbox-cli` (import path: `wealthbox_tools`). Both `wbox` and `wb` are registered as CLI entry points.

## Commands

```bash
# Install from PyPI
pip install wealthbox-cli

# Install (editable with dev deps)
pip install -e ".[dev]"

# Run tests
pytest

# Run a single test
pytest tests/path/to/test_file.py::test_name

# Lint
ruff check src/ tests/

# Use the CLI
wbox <resource> <command> [options]
```

**Command shape note:** `users` and `activity` use explicit list subcommands (`wbox users list`, `wbox activity list`).

**Activity pagination note:** `/activity` is cursor-based. Use `--cursor` for subsequent pages; do not add `page`/`per_page` parameters for activity queries.

**Authentication:** Token is resolved in this order (first wins):
1. `--token` flag (hidden, not shown in `--help`)
2. `WEALTHBOX_TOKEN` environment variable
3. Config file via `wbox config set-token` (~/.config/wbox/config.json or %APPDATA%\wbox\config.json)
4. `.env` file in working directory (auto-loaded via python-dotenv)

**Config commands:** `wbox config set-token` (prompt + store), `wbox config show` (display masked), `wbox config clear` (remove). Implementation: `cli/_config.py` (storage helper) and `cli/config.py` (Typer commands).

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

**`add` command pattern:** Create commands are named `add` (not `create`). They take structured flags instead of a raw JSON positional argument. `contacts add` is now a subcommand group with type-specific commands: `contacts add person`, `contacts add household`, `contacts add org`, and `contacts add trust`. Contacts/tasks/projects/opportunities/workflows expose a `--more-fields` JSON-object escape hatch for uncommon fields; it may not override fields that already have explicit CLI flags.

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

**Authentication:** Token resolution is handled in `get_client()` in `cli/_util.py`: flag > env var > config file > .env. The resolved token is passed as `ACCESS_TOKEN` HTTP header. Rate limiting is sliding-window (300 req / 5-min window); state persists across processes via `~/.wbox_rate_limit.json`. 429 responses trigger automatic retry with logging on malformed `Retry-After` headers.

**Models:** Input models live in `models/` (e.g., `ContactCreateInput`, `TaskListQuery`). List queries use `exclude_none=True`; update inputs use `exclude_unset=True` to preserve explicit nulls. Enums use Python 3.11+ `StrEnum`. `RequireAnyFieldModel` (in `models/common.py`) rejects empty update payloads. `OutputFormat` (in `cli/_util.py`) is a CLI-layer enum — not a model.

**Model validation patterns:** Use `Field(ge=1)` for all positive-int ID fields. Use `DateField` (YYYY-MM-DD) and `DateTimeField` (ISO 8601) `Annotated` type aliases from `models/common.py` for date/datetime string fields — import them explicitly in each model file that uses them (Pydantic evaluates annotation strings against the module's globals; missing imports cause a "not fully defined" error at runtime). `updated_since`/`updated_before`/`deleted_since` filter params are `DateTimeField`, not `DateField`.

**Wealthbox datetime format:** Datetime fields use ISO 8601: `YYYY-MM-DDTHH:MM:SS-07:00` or `YYYY-MM-DDTHH:MM:SSZ`. Date-only fields (birth_date, etc.) use `YYYY-MM-DD`. See `resources/api_examples/` for canonical field examples per record type.

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

## CI/CD and Releasing

**CI:** `.github/workflows/ci.yml` — single workflow with three jobs:
- `lint` — `ruff check src/ tests/` (Python 3.12)
- `test` — `pytest` across Python 3.11, 3.12, 3.13
- `publish` — builds and publishes to PyPI via trusted publishers (OIDC), runs only on `v*` tags after lint + test pass

**To release a new version:**
1. Bump `version` in `pyproject.toml`
2. `pip install -e ".[dev]"` and verify `wbox --version`
3. Run `ruff check src/ tests/` and `pytest` — both must pass
4. Commit: `vX.Y.Z: <description>`
5. Tag: `git tag vX.Y.Z`
6. Push: `git push origin main --tags`
7. CI auto-publishes to PyPI

**PyPI project:** `wealthbox-cli` on pypi.org. Trusted publisher is configured for `massive-value/wealthbox-cli` workflow `ci.yml` with environment `pypi`. Do not change the workflow filename or the `environment: pypi` line without updating PyPI's trusted publisher config.

**Version convention:** Semantic versioning. Bump patch for fixes, minor for features, major for breaking changes.

## Key Files

- `src/wealthbox_tools/cli/main.py` — registers all sub-apps (including `config`)
- `src/wealthbox_tools/cli/_util.py` — `get_client` (token resolution), `run_client`, `handle_errors`, `output_result`, `make_category_command`, `build_linked_to`, `active_to_status`, `OutputFormat` (StrEnum: json/table/csv/tsv); tabular helpers: `_flatten_record`, `_extract_collection`, `_render_table`, `_render_kv_table`, `_render_dsv`
- `src/wealthbox_tools/cli/_config.py` — config file helpers: `load_config`, `save_config`, `get_stored_token`, `_config_dir`, `_config_path`
- `src/wealthbox_tools/cli/config.py` — `wbox config` commands: `set-token`, `show`, `clear`
- `src/wealthbox_tools/client/base.py` — `_WealthboxBase`, `WealthboxAPIError`, `RateLimiter`
  - `fetch_all_pages(path, params, collection_key, on_progress)` — shared full-dataset paginator; all `list_all_*` methods delegate here
- `src/wealthbox_tools/client/__init__.py` — `WealthboxClient` (combined mixins)
- `src/wealthbox_tools/models/common.py` — base classes: `WealthboxModel`, `RequireAnyFieldModel`, `PaginationQuery`, `LinkedToRef`; validation helpers: `DateField`, `DateTimeField` (Annotated type aliases), `_DATETIME_ISO_RE`, `_DATETIME_EXAMPLE`
- `src/wealthbox_tools/models/enums.py` — all enum definitions
- `resources/api_examples/` — canonical JSON examples for each record type's create/update payloads; use as reference when adding fields or validators
- `tests/conftest.py` — shared `runner` fixture and `mock_token` autouse fixture
