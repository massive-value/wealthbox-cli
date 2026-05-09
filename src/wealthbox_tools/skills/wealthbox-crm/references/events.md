# Events

Calendar events with start/end times. Can be linked to contacts, projects, and opportunities.

## List Events

```bash
wbox events list [OPTIONS]
```

| Flag | Type | Description |
|------|------|-------------|
| `--resource-id` | INT | Filter by linked resource ID |
| `--resource-type` | Contact\|Project\|Opportunity | Type of linked resource |
| `--start-date-min` | ISO datetime | Events starting after |
| `--start-date-max` | ISO datetime | Events starting before |
| `--order` | asc\|desc\|recent\|created | Sort order |
| `--updated-since` | ISO datetime | Modified after |
| `--updated-before` | ISO datetime | Modified before |
| `--page` | INT | Page number |
| `--per-page` | INT | Results per page |
| `--verbose`, `-v` | flag | Show all fields |
| `--format` | json\|table\|csv\|tsv | Output format |

## Get Event

```bash
wbox events <ID>
wbox events get <ID>
```

Supports `--no-comments`, `--verbose`, `--format`.

## Create Event

```bash
wbox events add <TITLE> [OPTIONS]
```

| Flag | Type | Description |
|------|------|-------------|
| `<TITLE>` | positional | Event title (required) |
| `--starts-at` | ISO datetime | Start time (required) |
| `--ends-at` | ISO datetime | End time (required) |
| `--location` | STR | Location |
| `--state` | unconfirmed\|confirmed\|tentative\|completed\|cancelled | Event state |
| `--all-day` / `--no-all-day` | flag | All-day event |
| `--description` | STR | Description |
| `--category` | INT | Event category ID |
| `--contact` | INT | Link to contact |
| `--project` | INT | Link to project |
| `--opportunity` | INT | Link to opportunity |
| `--format` | json\|table\|csv\|tsv | Output format |

## Update Event

```bash
wbox events update <ID> [OPTIONS]
```

All create flags available, plus `--title` to rename. Only pass changed fields.

## Delete Event

```bash
wbox events delete <ID>
```

## Event Categories

```bash
wbox events categories
```

## Generated Flag Reference

The following section is auto-generated from the Typer command tree by
`wbox internals regen-skill-refs`. Do not hand-edit between the markers —
edits will be overwritten on the next regen pass.

<!-- auto-gen:flags -->
### `wbox events add`

Create a new event.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--all-day` / `--no-all-day` | `BOOLEAN` | `-` |  |
| `--category` | `INTEGER` | `-` | Event category ID |
| `--contact` | `INTEGER` | `-` | Link to a Contact by ID |
| `--description` | `TEXT` | `-` |  |
| `--ends-at` | `TEXT` | `-` | End datetime in ISO 8601, e.g. 2026-01-15T11:00:00-07:00 |
| `--format` | `CHOICE` | `json` |  |
| `--location` | `TEXT` | `-` |  |
| `--opportunity` | `INTEGER` | `-` | Link to an Opportunity by ID |
| `--project` | `INTEGER` | `-` | Link to a Project by ID |
| `--starts-at` | `TEXT` | `-` | Start datetime in ISO 8601, e.g. 2026-01-15T10:00:00-07:00 |
| `--state` | `CHOICE` | `-` | unconfirmed, confirmed, tentative, completed, cancelled |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

**Choices for `--state`:**

- `cancelled`
- `completed`
- `confirmed`
- `tentative`
- `unconfirmed`

### `wbox events categories`

List event category options.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--format` | `CHOICE` | `json` |  |
| `--page` | `INTEGER` | `-` | Page number |
| `--per-page` | `INTEGER` | `-` | Results per page (max 100) |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

### `wbox events delete`

Delete an existing event.

_No flags._

### `wbox events get`

Get a single event by ID.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--format` | `CHOICE` | `json` |  |
| `--no-comments` | `BOOLEAN` | `false` | Omit comments from output |
| `--verbose` / `-v` | `BOOLEAN` | `false` | Show all fields |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

### `wbox events list`

List events with optional filters.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--format` | `CHOICE` | `json` |  |
| `--order` | `CHOICE` | `-` | Sort order: asc, desc, recent, created |
| `--page` | `INTEGER` | `-` | Page number |
| `--per-page` | `INTEGER` | `-` | Results per page (max 100) |
| `--resource-id` | `INTEGER` | `-` | Filter by resource ID |
| `--resource-type` | `CHOICE` | `-` | Supports: Contact, Project, Opportunity |
| `--start-date-max` | `TEXT` | `-` | Format example: '2015-05-24 10:00 AM -0400' |
| `--start-date-min` | `TEXT` | `-` | Format example: '2015-05-24 10:00 AM -0400' |
| `--updated-before` | `TEXT` | `-` | Format example: '2015-05-24 10:00 AM -0400' |
| `--updated-since` | `TEXT` | `-` | Format example: '2015-05-24 10:00 AM -0400' |
| `--verbose` / `-v` | `BOOLEAN` | `false` | Show all fields |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

**Choices for `--order`:**

- `asc`
- `created`
- `desc`
- `recent`

**Choices for `--resource-type`:**

- `Contact`
- `Opportunity`
- `Project`

### `wbox events update`

Update an existing event. Pass only the fields you want to change.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--all-day` / `--no-all-day` | `BOOLEAN` | `-` |  |
| `--category` | `INTEGER` | `-` | Event category ID |
| `--contact` | `INTEGER` | `-` | Replace linked Contact (by ID) |
| `--description` | `TEXT` | `-` |  |
| `--ends-at` | `TEXT` | `-` | End datetime in ISO 8601, e.g. 2026-01-15T11:00:00-07:00 |
| `--format` | `CHOICE` | `json` |  |
| `--location` | `TEXT` | `-` |  |
| `--opportunity` | `INTEGER` | `-` | Replace linked Opportunity (by ID) |
| `--project` | `INTEGER` | `-` | Replace linked Project (by ID) |
| `--starts-at` | `TEXT` | `-` | Start datetime in ISO 8601, e.g. 2026-01-15T10:00:00-07:00 |
| `--state` | `CHOICE` | `-` | unconfirmed, confirmed, tentative, completed, cancelled |
| `--title` | `TEXT` | `-` | Event title |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

**Choices for `--state`:**

- `cancelled`
- `completed`
- `confirmed`
- `tentative`
- `unconfirmed`
<!-- /auto-gen:flags -->

## Examples

```bash
# Schedule a client meeting
wbox events add "Annual Review — Jane Doe" \
  --starts-at "2026-04-15T10:00:00-05:00" \
  --ends-at "2026-04-15T11:00:00-05:00" \
  --location "Office" \
  --state confirmed \
  --contact 12345

# List this week's events
wbox events list --start-date-min "2026-04-01T00:00:00Z" --start-date-max "2026-04-07T23:59:59Z" --format table
```
