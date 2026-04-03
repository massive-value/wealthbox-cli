# Contributing to Wealthbox CLI

Thank you for your interest in contributing to **wealthbox-cli**!

---

## Development Setup

```bash
git clone https://github.com/massive-value/wealthbox-cli
cd wealthbox-cli
python -m venv .venv
```

Activate the virtual environment:

| Platform | Command |
|----------|---------|
| macOS/Linux | `source .venv/bin/activate` |
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` |
| Windows (Command Prompt) | `.venv\Scripts\activate.bat` |

Then install with dev dependencies:

```bash
pip install -e ".[dev]"
```

Configure your Wealthbox API token (optional — tests don't require a real token):

```bash
wbox config set-token
```

---

## Running Tests

```bash
pytest
```

Tests use [respx](https://lundberg.github.io/respx/) to mock HTTP at the transport layer — no real API calls are made.

## Code Style

```bash
ruff check src/ tests/
```

- **ruff** for linting (E, F, I rules; 120-char line length)
- **mypy** in strict mode

---

## Project Architecture

Three layers under `src/wealthbox_tools/`:

| Layer | Purpose |
|-------|---------|
| `cli/` | [Typer](https://typer.tiangolo.com/) commands — user-facing, delegates to client |
| `client/` | Async HTTP client built from [httpx](https://www.python-httpx.org/) mixins |
| `models/` | [Pydantic v2](https://docs.pydantic.dev/) models for input validation |

`WealthboxClient` (in `client/__init__.py`) inherits from all resource mixins plus `_WealthboxBase` (core HTTP, rate limiting, error handling).

---

## Adding a New Resource

1. Add Pydantic models to `models/<resource>.py` (CreateInput, UpdateInput, ListQuery)
2. Add a client mixin to `client/<resource>.py` with async CRUD methods
3. Register the mixin in `client/__init__.py`
4. Add CLI commands to `cli/<resource>.py`
5. Register the CLI sub-app in `cli/main.py`
6. Add category types via `make_category_command()` if applicable
7. Add tests in `tests/test_<resource>_create.py` and `tests/test_<resource>_update.py`

---

## CI

Pull requests and pushes to `main` run GitHub Actions CI:

- **Lint:** `ruff check src/ tests/`
- **Test:** `pytest` across Python 3.11, 3.12, 3.13

Both must pass before merging.

---

## Pull Requests

- Keep PRs focused — one feature or fix per PR
- All tests must pass
- No ruff errors
- Update the CLI reference docs if commands change

---

## Reporting Issues

Open an issue at [github.com/massive-value/wealthbox-cli/issues](https://github.com/massive-value/wealthbox-cli/issues) with steps to reproduce, expected behavior, and actual behavior.
