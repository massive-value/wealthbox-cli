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
