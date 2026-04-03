# CLI Command Reference

Full command reference for the `wbox` CLI. For project overview, installation, and configuration see the [Getting Started](getting-started.md) guide.

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

## Output Formats

All list and get commands accept `--format [json|table|csv|tsv]` (default: `json`).

``` bash
# Terminal table (bordered grid, good for interactive use)
wbox contacts list --format table
wbox contacts get 123 --format table

# CSV — pipe to a file for Excel/Sheets
wbox contacts list --format csv > contacts.csv

# TSV
wbox tasks list --format tsv > tasks.tsv
```

**Single-object commands** (e.g. `get`) render as a two-column Field/Value table.
**List commands** render as a row-per-record table and print `Showing N of M results` to stderr when a total count is available.

**Nested field flattening:** Tabular output automatically flattens nested API structures so columns stay readable:

| Field type | Raw API value | Flattened |
|---|---|---|
| `linked_to` | `[{"id": 12, "type": "Contact"}]` | `Contact:12` |
| `email_addresses` | `[{"address": "a@b.com", "principal": true, ...}]` | `a@b.com` |
| `tags` | `["VIP", "Prospect"]` | `VIP, Prospect` |
| `custom_fields` | `[{...}, {...}]` | `[2 items]` |

Use `--verbose` with tabular formats to include all fields (same as JSON verbose mode).

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
wbox contacts list --updated-since "2025-01-01T00:00:00Z"
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

Contact creation is type-specific via subcommands:

``` bash
wbox contacts add person --first-name "John" --last-name "Doe" --contact-type "Client"
wbox contacts add person --first-name "Jane" --email jane@example.com --email-type "Work"
wbox contacts add household --name "Smith Family" --active
wbox contacts add org --name "Acme Corp" --contact-type "Prospect"
wbox contacts add trust --name "Bullock Family Trust" --contact-type "Client"
```

Person contacts also expose person-specific flags:

``` bash
wbox contacts add person \
  --first-name "Jane" \
  --last-name "Doe" \
  --prefix "Dr." \
  --nickname "Janie" \
  --gender "Female" \
  --marital-status "Married" \
  --birth-date "1980-01-15" \
  --anniversary "2005-06-10"
```

For uncommon fields not covered by direct flags, use `--more-fields` with a JSON object. It is merged with the explicit flags but cannot override them:

``` bash
wbox contacts add person --first-name "Jane" --more-fields '{"background_information": "VIP prospect", "client_since": "2020-01-01"}'
wbox contacts add household --name "Smith Family" --more-fields '{"important_information": "Prefers email"}'
```

Use `background_information` (not `background_info`) for contact payloads.

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
wbox tasks list --updated-since "2025-01-01T00:00:00Z"
```

### Categories

``` bash
wbox tasks categories
```

### Add

``` bash
wbox tasks add "Send proposal" --due-date "2026-03-20T09:00:00-07:00"
wbox tasks add "Follow up call" --frame tomorrow
wbox tasks add "Review documents" --due-date "2026-03-20T09:00:00-07:00" --priority High --contact <contact_id>
wbox tasks add "Team meeting" --frame today --assigned-to <user_id>
```

Use `--more-fields` for uncommon fields not covered by direct flags. It must be a JSON object and cannot shadow explicit CLI args like `name`, `due_date`, `frame`, `priority`, `assigned_to`, or resource links:

``` bash
wbox tasks add "Quarterly review" --due-date "2026-03-20T09:00:00-07:00" --more-fields '{"category": 123, "description": "Annual review meeting"}'
```

### Get

``` bash
wbox tasks get <task_id>
```

### Update

Pass only the fields you want to change:

``` bash
wbox tasks update <task_id> --name "Updated task name"
wbox tasks update <task_id> --due-date "2026-04-01T09:00:00-07:00"
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
wbox events add "Annual Review" --starts-at "2026-04-01T10:00:00-07:00" --ends-at "2026-04-01T11:00:00-07:00"
wbox events add "Client Meeting" --starts-at "2026-04-01T10:00:00-07:00" --ends-at "2026-04-01T11:00:00-07:00" --location "Office" --contact <contact_id>
wbox events add "All-day event" --starts-at "2026-04-01T10:00:00-07:00" --ends-at "2026-04-01T11:00:00-07:00" --all-day --state confirmed
```

### Get

``` bash
wbox events get <event_id>
```

### Update

Pass only the fields you want to change:

``` bash
wbox events update <event_id> --title "Rescheduled Review"
wbox events update <event_id> --starts-at "2026-05-01T10:00:00-07:00" --ends-at "2026-05-01T11:00:00-07:00"
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
wbox notes list --updated-since "2025-01-01T00:00:00Z"
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
