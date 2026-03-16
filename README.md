# Wealthbox CLI

A command-line interface for interacting with the Wealthbox CRM API.

This tool provides structured access to contacts, households, tasks,
events, notes, users, categories, and more — directly from your
terminal.

Official API documentation: https://dev.wealthbox.com

------------------------------------------------------------------------

## Features

-   Full CRUD support for:
    -   Contacts (Person, Household, Organization, Trust)
    -   Households (member management)
    -   Tasks
    -   Events
    -   Notes (create, read, update — delete not supported by API)
-   Structured flag-based `add` and `update` commands — no raw JSON required
-   `--json` escape hatch on contacts for complex nested payloads
-   Category and metadata lookups (resource-scoped and workspace-level)
-   Client-side filters for fields the API doesn't support server-side (e.g. `--assigned-to` on contacts)
-   Modular CLI structure with extensible client + model architecture

------------------------------------------------------------------------

## Installation

### 1. Clone the Repository

``` bash
git clone <your-repo-url>
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

Set your Wealthbox API token as an environment variable:

**macOS/Linux**

``` bash
export WEALTHBOX_TOKEN="your_api_token_here"
```

**Windows (PowerShell)**

``` powershell
setx WEALTHBOX_TOKEN "your_api_token_here"
```

Or place a `.env` file in the project root:

```
WEALTHBOX_TOKEN=your_api_token_here
```

------------------------------------------------------------------------

## Usage

``` bash
wbox <resource> <command> [options]
wb <resource> <command> [options]
```

For the full command reference see [docs/cli-reference.md](docs/cli-reference.md).

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

------------------------------------------------------------------------

## Troubleshooting

**401 Unauthorized** — Check your API token.

**Date format errors** — Wealthbox expects `"YYYY-MM-DD HH:MM AM/PM -OFFSET"` (e.g. `"2026-04-01 10:00 AM -0700"`).

**Add/Update appears to succeed but nothing changed** —
Some category-constrained writes can silently no-op (return success while leaving fields unchanged).
Verify by inspecting the returned JSON — `add` and `update` commands print the full object on success. Treat unchanged intended fields as a failed write.
Before category-constrained writes, discover valid values first (e.g. `wbox contacts categories contact-types`).

------------------------------------------------------------------------

## Disclaimer

This CLI wraps the Wealthbox API. Behavior depends on API version and
your account permissions.

Test destructive operations carefully.
