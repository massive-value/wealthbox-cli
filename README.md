# Wealthbox CLI

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

A command-line interface for interacting with the Wealthbox CRM API.

This tool provides structured access to contacts, households, tasks,
events, notes, users, categories, and more — directly from your
terminal.

Official API documentation: https://dev.wealthbox.com

> **Disclaimer:** This is an unofficial, community-built tool. It is not affiliated with,
> endorsed by, or supported by Wealthbox or its parent company. "Wealthbox" is a trademark
> of its respective owner.

------------------------------------------------------------------------

## Features

-   Full CRUD support for:
    -   Contacts (Person, Household, Organization, Trust)
    -   Households (member management)
    -   Tasks
    -   Events
    -   Notes (create, read, update — delete not supported by API)
-   Structured flag-based `add` and `update` commands — no raw JSON required
-   Type-specific contact creation subcommands: `contacts add person|household|org|trust`
-   `--more-fields` escape hatch on contacts/tasks/projects/opportunities/workflows for uncommon JSON fields
-   Multiple output formats via `--format`: `json` (default), `table`, `csv`, `tsv`
-   Nested API fields (linked_to, email_addresses, tags, etc.) automatically flattened for tabular output
-   Category and metadata lookups (resource-scoped and workspace-level)
-   Client-side filters for fields the API doesn't support server-side (e.g. `--assigned-to` on contacts)
-   Modular CLI structure with extensible client + model architecture

------------------------------------------------------------------------

## Installation

### 1. Clone the Repository

``` bash
git clone https://github.com/massive-value/wealthbox-cli
cd wealthbox-cli
```

### 2. Install (Recommended: Virtual Environment)

``` bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# OR
.venv\Scripts\activate     # Windows
```

Then install:

``` bash
pip install -e .
```

------------------------------------------------------------------------

## Configuration

Copy `.env.example` to `.env` and fill in your token:

```
WEALTHBOX_TOKEN=your_api_token_here
```

Or set it as an environment variable:

**macOS/Linux**

``` bash
export WEALTHBOX_TOKEN="your_api_token_here"
```

**Windows (PowerShell)**

``` powershell
setx WEALTHBOX_TOKEN "your_api_token_here"
```

------------------------------------------------------------------------

## Usage

``` bash
wbox <resource> <command> [options]
wb <resource> <command> [options]
```

For the full command reference see [docs/cli-reference.md](docs/cli-reference.md).

### Local wrapper

For this workspace, the easiest entrypoint is:

```bash
./run-wbox.sh me --format json
./run-wbox.sh users list --format json
./run-wbox.sh contacts list --per-page 1 --format json
./run-wbox.sh contacts add person --first-name Jane --last-name Doe --format json
```

The wrapper:
- loads `.env`
- uses the repo-local `.venv`
- runs the installed `wbox` CLI

------------------------------------------------------------------------

## Project Structure

    src/
      wealthbox_tools/
        cli/        # Typer commands — user-facing, delegates to client
        client/     # Async HTTP client built from mixins
        models/     # Pydantic v2 models for input validation
    tests/          # pytest integration tests (respx mocks)

**Client mixin pattern:** `WealthboxClient` inherits from resource mixins (`ContactsMixin`, `TasksMixin`, `EventsMixin`, etc.) plus `_WealthboxBase` (core HTTP, rate limiting, error handling). To add a new resource, create a mixin and register it in `client/__init__.py`.

**Rate limiting:** Sliding-window (300 req / 5-min window); state persists across processes via `~/.wbox_rate_limit.json`. 429 responses trigger automatic retry.

------------------------------------------------------------------------

## Development

``` bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run a single test
pytest tests/path/to/test_file.py::test_name
```

### Recommended local workflow

```bash
cd ~/.openclaw/workspace/integrations/wealthbox-cli

# Sync latest code
git pull

# Refresh editable install
.venv/bin/pip install -e .

# Run the read-only smoke test
./smoke_test.sh
```

Smoke test coverage:
- `wbox me`
- `wbox users list`
- `wbox contacts list --per-page 1`

This is intentionally read-only and meant to catch:
- token/config issues
- CLI install issues
- basic Wealthbox API access issues

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full contributor guide.

------------------------------------------------------------------------

## Troubleshooting

**401 Unauthorized** — Check your API token.

**Date format errors** — Wealthbox expects `"YYYY-MM-DD HH:MM AM/PM -OFFSET"` (e.g. `"2026-04-01 10:00 AM -0700"`).

**Add/Update appears to succeed but nothing changed** —
Some category-constrained writes can silently no-op (return success while leaving fields unchanged).
Verify by inspecting the returned JSON — `add` and `update` commands print the full object on success. Treat unchanged intended fields as a failed write.
Before category-constrained writes, discover valid values first (e.g. `wbox contacts categories contact-types`).

**`contacts add` examples no longer work if they use `Person`/`Household`/`Organization`/`Trust` as a positional argument** —
Use the new type-specific subcommands instead: `wbox contacts add person|household|org|trust ...`.

------------------------------------------------------------------------

## Disclaimer

This is an **unofficial, community-built** tool. It is not affiliated with, endorsed by,
or supported by Wealthbox or its parent company. "Wealthbox" is a trademark of its
respective owner. Use of this tool is subject to the [Wealthbox API Terms of Service](https://dev.wealthbox.com).

This CLI wraps the Wealthbox API. Behavior depends on API version and your account
permissions. Test destructive operations carefully.

------------------------------------------------------------------------

## License

Apache 2.0 — see [LICENSE](LICENSE).
