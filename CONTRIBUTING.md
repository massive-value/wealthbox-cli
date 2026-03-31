# Contributing to wealthbox-cli

Thank you for your interest in contributing!

## Development Setup

```bash
git clone https://github.com/massive-value/wealthbox-cli
cd wealthbox-cli
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# OR
.venv\Scripts\activate     # Windows

pip install -e ".[dev]"
```

Configure your Wealthbox API token:

```bash
wbox config set-token
```

Or copy `.env.example` to `.env` and add your token there.

## Running Tests

```bash
pytest
```

Tests use `respx` to mock HTTP at the transport layer — no real API calls are made.

## Code Style

```bash
ruff check src/
mypy src/
```

- **ruff** for linting (E, F, I rules; 120-char line length)
- **mypy** in strict mode (has known `untyped-decorator` warnings from Typer — not currently enforced in CI)

## Project Architecture

Three layers under `src/wealthbox_tools/`:

- `cli/` — Typer commands; user-facing, delegates to client
- `client/` — Async HTTP client built from mixins
- `models/` — Pydantic v2 models for input validation

`WealthboxClient` (in `client/__init__.py`) inherits from all resource mixins plus `_WealthboxBase` (core HTTP, rate limiting, error handling).

## Adding a New Resource

1. Add Pydantic models to `models/<resource>.py` (CreateInput, UpdateInput, ListQuery)
2. Add a client mixin to `client/<resource>.py` with async CRUD methods; add `list_all_<resource>()` if full-dataset fetches are needed (delegates to `fetch_all_pages()`)
3. Register the mixin in `client/__init__.py`
4. Add CLI commands to `cli/<resource>.py` following the patterns in existing modules (e.g. `cli/tasks.py`)
5. Register the CLI sub-app in `cli/main.py`
6. If the resource has category types, add them via `make_category_command()` in the resource's `categories` sub-app
7. Add tests in `tests/test_<resource>_create.py` and `tests/test_<resource>_update.py`

## CI

Pull requests and pushes to `main` run GitHub Actions CI:

- **Lint:** `ruff check src/ tests/`
- **Test:** `pytest` across Python 3.11, 3.12, 3.13

Both must pass before merging.

## Pull Requests

- Keep PRs focused — one feature or fix per PR
- All tests must pass (`pytest`)
- No ruff errors
- Update the CLI reference docs if commands change

## Reporting Issues

Open an issue at https://github.com/massive-value/wealthbox-cli/issues with steps to reproduce, expected behavior, and actual behavior.
