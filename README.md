# Wealthbox CLI

A command-line interface for interacting with the Wealthbox CRM API.

This tool provides structured access to contacts, households, tasks,
events, notes, users, categories, and more --- directly from your
terminal.

Official API documentation: - https://www.wealthbox.com/api/ -
https://dev.wealthbox.com

------------------------------------------------------------------------

## Features

-   Full CRUD support for:
    -   Contacts
    -   Households
    -   Tasks
    -   Events
    -   Notes (create, read, update --- delete not supported by API)
-   Category and metadata lookups
-   Filtering and query parameters
-   JSON-based advanced field support
-   Modular CLI structure
-   Extensible client + model architecture

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
```

------------------------------------------------------------------------

## Contacts

``` bash
wbox contacts list
```

------------------------------------------------------------------------

## Households

Add member:

``` bash
wbox households add-member <household_id>   --member-id <person_contact_id>   --title "Head|Spouse|Parent|Other Dependent|Child|Sibling|Partner|Grandchild|Grandparent"
```

Remove member:

``` bash
wbox households remove-member <household_id>   --member-id <person_contact_id>
```

------------------------------------------------------------------------

## Tasks

### Categories

``` bash
wbox tasks categories
```

### Create

``` bash
wbox tasks create "Task Name"   --frame "today"   --more-fields '{"linked_to": [{"id": 30776510, "type": "Contact"}]}'
```

### Get

``` bash
wbox tasks get <task_id>
```

### Update

``` bash
wbox tasks update <task_id> '{"name": "Updated Name", "frame": "tomorrow"}'
```

### Delete

``` bash
wbox tasks delete <task_id>
```

### List with Filters

``` bash
wbox tasks list   --resource-id <id>   --resource-type <Contact|Opportunity|Project>   --assigned-to <user_id>   --assigned-to-team <team_id>   --created-by <user_id>   --completed true|false   --task-type <type_id>   --updated-since YYYY-MM-DD   --updated-before YYYY-MM-DD
```

------------------------------------------------------------------------

## Events

### Categories

``` bash
wbox events categories
```

### List

``` bash
wbox events list   --resource-id <id>   --resource-type <Contact|Opportunity|Project>   --start-date-min YYYY-MM-DD   --start-date-max YYYY-MM-DD   --order asc|desc|recent|created   --updated-since YYYY-MM-DD   --updated-before YYYY-MM-DD
```

### Create

``` bash
wbox events create '{
  "title": "Test Event",
  "starts_at": "2026-02-27 11:00 AM -0700",
  "ends_at": "2026-02-27 12:00 PM -0700",
  "linked_to": [{"id": 30776510, "type": "Contact"}],
  "invitees": [{"id": 152760, "type": "User"}]
}'
```

### Get

``` bash
wbox events get <event_id>
```

### Update

``` bash
wbox events update <event_id> '{"state": "confirmed", "location": "Office"}'
```

### Delete

``` bash
wbox events delete <event_id>
```

------------------------------------------------------------------------

## Notes

### Create

``` bash
wbox notes create '{
  "content": "Test note",
  "linked_to": [{"id": 30776510, "type": "Contact"}]
}'
```

### Get

``` bash
wbox notes get <note_id>
```

### Update

``` bash
wbox notes update <note_id> '{"content": "Updated content"}'
```

Note: Deleting notes is not supported via the Wealthbox v1 API.

### List

``` bash
wbox notes list   --resource-id <id>   --resource-type <Contact|Opportunity|Project>   --order asc|desc|recent|created   --updated-since YYYY-MM-DD   --updated-before YYYY-MM-DD
```

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
```

Filter and paginate:

``` bash
wbox categories custom-fields \
  --document-type Contact|Opportunity|Project|Task|Event|ManualInvestmentAccount|DataFile \
  --page 1 --per-page 50
```

All category list commands now support pagination via `--page` and `--per-page`.

------------------------------------------------------------------------

## Project Structure

    src/
      wealthbox_tools/
        cli/        # CLI command definitions
        client/     # API client logic
        models/     # Data models and schemas

------------------------------------------------------------------------

## Troubleshooting

**401 Unauthorized** Check your API token.

**JSON Errors** Validate formatting and quoting.

**Unsupported `--format` value** Only `--format json` is supported. Unsupported values (for example `--format table`) now fail fast with a clear error.

**Date Errors** Use proper ISO or Wealthbox-supported formats.

**Create/Update appears to succeed but nothing changed**
Some category-constrained writes can silently no-op (return success while leaving fields unchanged).
Always verify writes with an immediate readback (`wbox <resource> get <id>`), and treat unchanged intended fields as a failed write.
Before category-constrained writes, discover valid values first (for example: `wbox contacts categories contact-sources`).

------------------------------------------------------------------------

## Disclaimer

This CLI wraps the Wealthbox API. Behavior depends on API version and
your account permissions.

Test destructive operations carefully.
