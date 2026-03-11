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

## Basic Usage

``` bash
wbox <resource> <command> [options]
```

Health checks:

``` bash
wbox me
wbox users list
wbox activity list
```

Activity feed pagination uses cursor-based navigation (not page/per-page):

``` bash
wbox activity list --cursor <cursor_from_previous_response>
wbox activity list --verbose   # show full body content (default truncates to 500 chars)
```

------------------------------------------------------------------------

## Contacts

### List

``` bash
wbox contacts list
wbox contacts list --type Person|Household|Organization|Trust
wbox contacts list --contact-type "Client"
wbox contacts list --name "Smith"
wbox contacts list --active
wbox contacts list --tags "tag1,tag2"
wbox contacts list --updated-since "2025-01-01"
wbox contacts list --per-page 100 --page 2
```

Filter by assigned user (fetches all pages client-side — the API has no server-side filter for this):

``` bash
wbox contacts list --assigned-to <user_id>
wbox contacts list --assigned-to <user_id> --type Household
```

Progress output goes to stderr, so the result stays pipeable:

``` bash
wbox contacts list --assigned-to <user_id> | jq '.contacts | length'
```

### Add

The record type is a required positional argument (case-insensitive):

``` bash
wbox contacts add Person --first-name John --last-name Doe --contact-type Client
wbox contacts add Person --first-name Jane --email jane@example.com --email-type Work
wbox contacts add Household --name "Smith Family" --active
wbox contacts add Organization --name "Acme Corp" --contact-type Prospect
```

For complex nested payloads (e.g. multiple email addresses), use `--json`:

``` bash
wbox contacts add --json '{"type": "Person", "first_name": "Jane", "email_addresses": [{"address": "jane@example.com", "kind": "Work", "principal": true}]}'
```

### Get

``` bash
wbox contacts get <contact_id>
wbox contacts get <contact_id> --verbose
```

### Update

Pass only the fields you want to change:

``` bash
wbox contacts update <contact_id> --contact-type Client
wbox contacts update <contact_id> --first-name Jonathan --last-name Smith
wbox contacts update <contact_id> --inactive
wbox contacts update <contact_id> --assigned-to <user_id>
```

For nested field updates (e.g. replacing email addresses), use `--json`:

``` bash
wbox contacts update <contact_id> --json '{"email_addresses": [{"address": "new@example.com", "kind": "Work", "principal": true}]}'
```

### Delete

``` bash
wbox contacts delete <contact_id>
```

### Contact Categories

``` bash
wbox contacts categories contact-types
wbox contacts categories contact-sources
wbox contacts categories email-types
wbox contacts categories phone-types
wbox contacts categories address-types
wbox contacts categories website-types
wbox contacts categories contact-roles
```

------------------------------------------------------------------------

## Households

Add member:

``` bash
wbox households add-member <household_id> <member_id> --title "Head|Spouse|Parent|Other Dependent|Child|Sibling|Partner|Grandchild|Grandparent"
```

Remove member:

``` bash
wbox households remove-member <household_id> <member_id>
```

------------------------------------------------------------------------

## Tasks

### List

``` bash
wbox tasks list
wbox tasks list --contact <id>
wbox tasks list --project <id>
wbox tasks list --opportunity <id>
wbox tasks list --assigned-to <user_id>
wbox tasks list --include-completed
wbox tasks list --updated-since "2025-01-01"
```

### Categories

``` bash
wbox tasks categories
```

### Add

``` bash
wbox tasks add "Send proposal" --due-date "2026-03-20 09:00 AM -0700"
wbox tasks add "Follow up call" --frame tomorrow
wbox tasks add "Review documents" --due-date "2026-03-20 09:00 AM -0700" --priority High --contact <contact_id>
wbox tasks add "Team meeting" --frame today --assigned-to <user_id>
```

Use `--more-fields` for uncommon fields not covered by direct flags:

``` bash
wbox tasks add "Quarterly review" --due-date "2026-03-20 09:00 AM -0700" --more-fields '{"category": 123, "description": "Annual review meeting"}'
```

### Get

``` bash
wbox tasks get <task_id>
```

### Update

Pass only the fields you want to change:

``` bash
wbox tasks update <task_id> --name "Updated task name"
wbox tasks update <task_id> --due-date "2026-04-01 09:00 AM -0700"
wbox tasks update <task_id> --priority High
wbox tasks update <task_id> --complete
wbox tasks update <task_id> --no-complete
wbox tasks update <task_id> --contact <contact_id>
```

### Delete

``` bash
wbox tasks delete <task_id>
```

------------------------------------------------------------------------

## Events

### List

``` bash
wbox events list
wbox events list --resource-id <id> --resource-type Contact|Opportunity|Project
wbox events list --start-date-min "2026-01-01" --start-date-max "2026-12-31"
wbox events list --order asc|desc|recent|created
```

### Categories

``` bash
wbox events categories
```

### Add

``` bash
wbox events add "Annual Review" --starts-at "2026-04-01 10:00 AM -0700" --ends-at "2026-04-01 11:00 AM -0700"
wbox events add "Client Meeting" --starts-at "2026-04-01 10:00 AM -0700" --ends-at "2026-04-01 11:00 AM -0700" --location "Office" --contact <contact_id>
wbox events add "All-day event" --starts-at "2026-04-01 10:00 AM -0700" --ends-at "2026-04-01 11:00 AM -0700" --all-day --state confirmed
```

### Get

``` bash
wbox events get <event_id>
```

### Update

Pass only the fields you want to change:

``` bash
wbox events update <event_id> --title "Rescheduled Review"
wbox events update <event_id> --starts-at "2026-05-01 10:00 AM -0700" --ends-at "2026-05-01 11:00 AM -0700"
wbox events update <event_id> --state cancelled
wbox events update <event_id> --location "Conference Room B"
```

### Delete

``` bash
wbox events delete <event_id>
```

------------------------------------------------------------------------

## Notes

### List

``` bash
wbox notes list
wbox notes list --contact <id>
wbox notes list --project <id>
wbox notes list --opportunity <id>
wbox notes list --updated-since "2025-01-01"
wbox notes list --verbose   # show full content (default truncates to 500 chars)
```

### Add

``` bash
wbox notes add "Portfolio review call"
wbox notes add "Discussed estate plan" --contact <contact_id>
wbox notes add "Project kickoff notes" --contact <contact_id> --project <project_id>
```

### Get

``` bash
wbox notes get <note_id>
```

### Update

Pass only the fields you want to change:

``` bash
wbox notes update <note_id> --content "Updated note content"
wbox notes update <note_id> --contact <contact_id>
```

Note: Deleting notes is not supported via the Wealthbox v1 API.

------------------------------------------------------------------------

## Categories & Metadata

``` bash
wbox categories tags
wbox categories file-categories
wbox categories opportunity-stages
wbox categories opportunity-pipelines
wbox categories investment-objectives
wbox categories financial-account-types
```

### Custom Fields

``` bash
wbox categories custom-fields
wbox categories custom-fields --document-type Contact|Opportunity|Project|Task|Event|ManualInvestmentAccount|DataFile
```

------------------------------------------------------------------------

## Project Structure

    src/
      wealthbox_tools/
        cli/        # Typer commands — user-facing, delegates to client
        client/     # Async HTTP client built from mixins
        models/     # Pydantic v2 models for input validation
    tests/          # pytest integration tests (respx mocks)

------------------------------------------------------------------------

## Troubleshooting

**401 Unauthorized** — Check your API token.

**Date format errors** — Wealthbox expects `"YYYY-MM-DD HH:MM AM/PM -OFFSET"` (e.g. `"2026-04-01 10:00 AM -0700"`).

**Create/Update appears to succeed but nothing changed** —
Some category-constrained writes can silently no-op (return success while leaving fields unchanged).
Always verify writes with an immediate readback (`wbox <resource> get <id>`), and treat unchanged intended fields as a failed write.
Before category-constrained writes, discover valid values first (e.g. `wbox contacts categories contact-types`).

------------------------------------------------------------------------

## Disclaimer

This CLI wraps the Wealthbox API. Behavior depends on API version and
your account permissions.

Test destructive operations carefully.
