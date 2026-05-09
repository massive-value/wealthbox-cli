# Tasks

Tasks track action items. Can be linked to contacts, projects, and opportunities.

## List Tasks

```bash
wbox tasks list [OPTIONS]
```

| Flag | Type | Description |
|------|------|-------------|
| `--contact` | INT | Filter by linked contact ID |
| `--project` | INT | Filter by linked project ID |
| `--opportunity` | INT | Filter by linked opportunity ID |
| `--assigned-to` | INT | Filter by assigned user ID |
| `--assigned-to-team` | INT | Filter by assigned team ID |
| `--created-by` | INT | Filter by creator user ID |
| `--include-completed` | flag | Include completed tasks (default: outstanding only) |
| `--type` | all\|parents\|subtasks | Filter by task type |
| `--updated-since` | ISO datetime | Modified after |
| `--updated-before` | ISO datetime | Modified before |
| `--page` | INT | Page number |
| `--per-page` | INT | Results per page |
| `--verbose`, `-v` | flag | Show all fields |
| `--format` | json\|table\|csv\|tsv | Output format |

## Get Task

```bash
wbox tasks <ID>
wbox tasks get <ID>
```

Supports `--no-comments`, `--verbose`, `--format`.

## Create Task

```bash
wbox tasks add <NAME> [OPTIONS]
```

| Flag | Type | Description |
|------|------|-------------|
| `<NAME>` | positional | Task name (required) |
| `--due-date` | STR | Due date (XOR with --frame) |
| `--frame` | today\|tomorrow\|this-week\|next-week\|future\|specific | Relative due date (XOR with --due-date). Both kebab-case (`next-week`) and snake_case (`next_week`) are accepted. |
| `--priority` | Low\|Medium\|High | Priority level |
| `--category` | STR | Task category by name or ID (e.g. "Follow-up"). See `wbox categories task-categories`. |
| `--description` | STR | Task description |
| `--assigned-to` | INT | Assign to user ID |
| `--contact` | INT | Link to contact |
| `--project` | INT | Link to project |
| `--opportunity` | INT | Link to opportunity |
| `--more-fields` | JSON | e.g. `{"complete": false, "assigned_to_team": 456}` |
| `--format` | json\|table\|csv\|tsv | Output format |

**Note:** `--due-date` and `--frame` are mutually exclusive. Use `--frame` for relative dates.

**Note (Wealthbox quirk):** `--frame next_week` resolves on the API side to the Monday of the calendar week *after* today. **If today is Sunday, `next_week` is tomorrow** (Monday) — only one day away, not seven. Wealthbox treats Sunday as the last day of the current week. If precise control matters (e.g. an advisor said "next week" expecting 7+ days out), use `--due-date YYYY-MM-DDTHH:MM:SS-07:00` with an explicit date instead of `--frame`.

## Update Task

```bash
wbox tasks update <ID> [OPTIONS]
```

| Flag | Type | Description |
|------|------|-------------|
| `--name` | STR | Rename |
| `--due-date` | STR | Change due date |
| `--frame` | STR | Change relative due date. Accepts kebab-case (`next-week`) or snake_case (`next_week`); see Note above re: Sunday boundary. |
| `--priority` | Low\|Medium\|High | Change priority |
| `--category` | STR | Task category by name or ID. See `wbox categories task-categories`. |
| `--assigned-to` | INT | Reassign |
| `--complete` / `--no-complete` | flag | Mark complete/incomplete |
| `--description` | STR | Update description |
| `--contact` | INT | Relink to contact |
| `--project` | INT | Relink to project |
| `--opportunity` | INT | Relink to opportunity |
| `--format` | json\|table\|csv\|tsv | Output format |

## Delete Task

```bash
wbox tasks delete <ID>
```

## Task Categories

```bash
wbox tasks categories
```

## Generated Flag Reference

The following section is auto-generated from the Typer command tree by
`wbox internals regen-skill-refs`. Do not hand-edit between the markers —
edits will be overwritten on the next regen pass.

<!-- auto-gen:flags -->
### `wbox tasks add`

Create a new task. Required: name, and either due_date or frame.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--assigned-to` | `INTEGER` | `-` | Assign to a user by ID |
| `--category` | `TEXT` | `-` | Task category by name or ID — see: wbox categories task-categories |
| `--contact` | `INTEGER` | `-` | Link to a Contact by ID |
| `--description` | `TEXT` | `-` | Task description |
| `--due-date` | `TEXT` | `-` | Example: '2025-05-24 10:00 AM -0700' (must match Wealthbox format) |
| `--format` | `CHOICE` | `json` |  |
| `--frame` | `_NORMALIZE_FRAME` | `-` | Friendly due timeframe. One of: today, tomorrow, this-week / this_week, next-week / next_week, future, specific. |
| `--more-fields` | `TEXT` | `-` | JSON: {"complete": false, "assigned_to_team": 456} |
| `--opportunity` | `INTEGER` | `-` | Link to an Opportunity by ID |
| `--priority` | `CHOICE` | `-` | Low, Medium, or High |
| `--project` | `INTEGER` | `-` | Link to a Project by ID |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

**Choices for `--priority`:**

- `High`
- `Low`
- `Medium`

### `wbox tasks categories`

List task category options.

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

### `wbox tasks delete`

Delete a task by ID.

_No flags._

### `wbox tasks get`

Get a single task by ID.

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

### `wbox tasks list`

List tasks with optional filters. By default only outstanding tasks are returned; use --include-completed to include completed tasks

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--assigned-to` | `INTEGER` | `-` | Filter by assigned user ID |
| `--assigned-to-team` | `INTEGER` | `-` | Filter by assigned team ID |
| `--contact` | `INTEGER` | `-` | Filter tasks linked to a Contact (by ID) |
| `--created-by` | `INTEGER` | `-` | Filter by creator user ID |
| `--format` | `CHOICE` | `json` |  |
| `--include-completed` | `BOOLEAN` | `false` | Include completed tasks (default returns outstanding tasks only) |
| `--opportunity` | `INTEGER` | `-` | Filter tasks linked to an Opportunity (by ID) |
| `--page` | `INTEGER` | `-` |  |
| `--per-page` | `INTEGER` | `-` | Results per page (max 100) |
| `--project` | `INTEGER` | `-` | Filter tasks linked to a Project (by ID) |
| `--type` | `CHOICE` | `-` | all, parents, subtasks |
| `--updated-before` | `TEXT` | `-` |  |
| `--updated-since` | `TEXT` | `-` |  |
| `--verbose` / `-v` | `BOOLEAN` | `false` | Show all fields |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

**Choices for `--type`:**

- `all`
- `parents`
- `subtasks`

### `wbox tasks update`

Update an existing task. Pass only the fields you want to change.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--assigned-to` | `INTEGER` | `-` | Reassign to a user by ID |
| `--category` | `TEXT` | `-` | Task category by name or ID — see: wbox categories task-categories |
| `--complete` / `--no-complete` | `BOOLEAN` | `-` | Mark as complete or incomplete |
| `--contact` | `INTEGER` | `-` | Replace linked Contact (by ID) |
| `--description` | `TEXT` | `-` |  |
| `--due-date` | `TEXT` | `-` | ISO 8601 datetime, e.g. '2026-04-01T09:00:00-07:00' |
| `--format` | `CHOICE` | `json` |  |
| `--frame` | `_NORMALIZE_FRAME` | `-` | Friendly due timeframe. One of: today, tomorrow, this-week / this_week, next-week / next_week, future, specific. |
| `--name` | `TEXT` | `-` | Task name |
| `--opportunity` | `INTEGER` | `-` | Replace linked Opportunity (by ID) |
| `--priority` | `CHOICE` | `-` | Low, Medium, or High |
| `--project` | `INTEGER` | `-` | Replace linked Project (by ID) |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

**Choices for `--priority`:**

- `High`
- `Low`
- `Medium`
<!-- /auto-gen:flags -->

## Examples

```bash
# Create a follow-up task linked to a contact
wbox tasks add "Follow up with Jane" --frame next-week --priority High --contact 12345

# List my outstanding tasks
wbox tasks list --assigned-to 67890 --format table

# Mark a task complete
wbox tasks update 111 --complete
```
