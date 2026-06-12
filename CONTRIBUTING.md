# Contributing to Wealthbox CLI

Thank you for your interest in contributing to **wealthbox-cli**!

---

## Development Setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management. Install it first if you don't have it:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
irm https://astral.sh/uv/install.ps1 | iex
```

Then clone and sync:

```bash
git clone https://github.com/massive-value/wealthbox-cli
cd wealthbox-cli
uv sync --extra dev
```

`uv sync` creates a project-local `.venv/` and installs the package in editable mode with dev dependencies. There is nothing to "activate" — prefix commands with `uv run`:

```bash
uv run wbox --version
uv run pytest
uv run ruff check src/ tests/
```

Configure your Wealthbox API token (optional — tests don't require a real token):

```bash
uv run wbox config set-token
```

> Prefer plain `pip`? `pip install -e ".[dev]"` still works — `pyproject.toml` is the source of truth for both tools.

---

## Pre-commit hooks

The repo ships a `.pre-commit-config.yaml` with three hooks: ruff lint, mypy strict, and a skill-ref drift check. Install them once after cloning:

```bash
# uv
uv tool install pre-commit
pre-commit install

# or pip
pip install pre-commit
pre-commit install
```

Run all hooks manually at any time:

```bash
pre-commit run --all-files
# or without a local install:
uv tool run pre-commit run --all-files
```

---

## Running Tests

```bash
uv run pytest
```

Tests use [respx](https://lundberg.github.io/respx/) to mock HTTP at the transport layer — no real API calls are made.

### Coverage gate

CI enforces `--cov-fail-under=91` on the ubuntu test leg. Run locally with:

```bash
uv run pytest --cov=src/wealthbox_tools --cov-report=term
```

## Code Style

```bash
uv run ruff check src/ tests/
```

- **ruff** for linting (E, F, I rules; 120-char line length)
- **mypy** in strict mode (`uv run mypy src/` must exit 0)

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

## Skill reference files

Any change to CLI command signatures or help text **must** regenerate the skill reference files before committing:

```bash
uv run wbox internals regen-skill-refs
git add src/wealthbox_tools/skills/wealthbox-crm/references/
```

The generated files live under `src/wealthbox_tools/skills/wealthbox-crm/references/` and are checked in. The `skill-ref-drift` CI job and the pre-commit hook both fail on stale refs.

---

## Standing verification

Run all of these before opening a PR (CI enforces each):

```bash
uv run ruff check src/ tests/
uv run pytest
uv run mypy src/
uv run wbox internals regen-skill-refs && git diff --exit-code -- src/wealthbox_tools/skills/wealthbox-crm/references/
```

---

## Releasing

Releases follow semantic versioning. Bump patch for fixes, minor for features, major for breaking changes.

1. Bump `version` in `pyproject.toml`.
2. Add a `## [X.Y.Z]` entry at the top of `CHANGELOG.md` (CI enforces that the changelog version matches `pyproject.toml` before publishing to PyPI).
3. Verify locally: `uv run ruff check src/ tests/ && uv run pytest && uv run mypy src/`
4. Commit: `vX.Y.Z: <description>`
5. Tag: `git tag vX.Y.Z`
6. Push: `git push origin main --tags`

CI builds and publishes to PyPI automatically on `v*` tags once lint, tests, typecheck, and skill-ref-drift all pass.

---

## CI

Pull requests and pushes to `main` run GitHub Actions CI:

- **Lint:** `ruff check src/ tests/`
- **Test:** `pytest` across Python 3.11, 3.12, 3.13 (ubuntu) + 3.12 (windows); coverage gate `--cov-fail-under=91` on ubuntu
- **Typecheck:** `mypy src/` (strict)
- **Smoke:** installs the built wheel in isolation (no dev deps) and runs `wbox --version` / `wbox notes --help`, catching missing-runtime-dependency startup crashes
- **Skill-ref drift:** regenerates refs and asserts no git diff

All jobs must pass before merging; `publish` (on `v*` tags) additionally gates on lint, test, typecheck, and smoke.

---

## Pull Requests

- Keep PRs focused — one feature or fix per PR
- All tests must pass
- No ruff errors
- Update the CLI reference docs if commands change

---

## Reporting Issues

Open an issue at [github.com/massive-value/wealthbox-cli/issues](https://github.com/massive-value/wealthbox-cli/issues) with steps to reproduce, expected behavior, and actual behavior.
