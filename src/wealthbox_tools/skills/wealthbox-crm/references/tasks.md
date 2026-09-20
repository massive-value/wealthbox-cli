# Tasks

Tasks track action items. Can be linked to contacts, projects, and opportunities.

## The default hides most of the data

`GET /tasks` returns **open tasks only** unless you say otherwise. In a firm with
5,174 tasks, 4,994 of them complete, the default shows 3% of the record set. The
API's `completed` parameter is a two-way switch, not an "include": omitted or
`false` means open only, `true` means completed only. No value returns both.

`wbox tasks list --status` names all three cases:

| `--status` | What you get | API calls |
|------------|--------------|-----------|
| `open` (default) | Incomplete tasks. Matches Wealthbox's own default. | 1 |
| `completed` | Completed tasks only. | 1 |
| `all` | Both, merged by `id`. | 2 |

Use `open` when the advisor asks what is outstanding. Use `all` when counting,
auditing, or searching history. `--include-completed` still works as a hidden
alias for `--status all`; it used to mean `completed=true`, which returned
completed tasks *only*, the opposite of its name.

## List Tasks

```bash
wbox tasks list [OPTIONS]
```

| Flag | Type | Description |
|------|------|-------------|
| `--contact` | INT | Filter by linked contact ID |
| `--project` | INT | Filter by linked project ID |
| `--opportunity` | INT | Filter by linked opportunity ID |
| `--assigned-to` | INT | Filter by assigned user ID — get yours via `wbox me user-id`, **not** `wbox me \| jq .id` (that's the login profile, which silently returns zero results). |
| `--assigned-to-team` | INT | Filter by assigned team ID. List team IDs with `wbox teams list`. |
| `--created-by` | INT | Filter by creator user ID |
| `--status` | open\|completed\|all | Which tasks to return. Default `open`. |
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
| `--custom-field` | NAME=VALUE | Set a custom field. Repeatable. See note below. |
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
| `--custom-field` | NAME=VALUE | Set a custom field. Repeatable. |
| `--format` | json\|table\|csv\|tsv | Output format |

## Custom fields

`--custom-field "Account Number=X-42"` takes the field's name or its numeric ID.
Repeat the flag for more than one. List what the workspace defines with:

```bash
wbox categories custom-fields --document-type Task
```

An unknown name is an error that lists the valid ones. That check matters:
Wealthbox accepts a custom-field payload keyed by name with a 200 response and
then discards it, so an unchecked write would look like it worked.

## Subtasks

Subtasks come back in the normal list with a `parent {id, type}` object, visible
under `--verbose`. Filter to them with `--type subtasks`. Their parent can be a
Task or a WorkflowStep. There is no flag for creating one: the API takes subtasks
only as inline objects nested in a parent task's create payload, so use
`--more-fields '{"subtasks": [{"name": "...", "due_date": "..."}]}'`.

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
| `--custom-field` | `TEXT` | `-` | Set a custom field as NAME=VALUE (repeatable). Name or numeric ID; see: wbox categories custom-fields --document-type Task |
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

List tasks with optional filters. Wealthbox returns open tasks only by default; use --status completed or --status all to see completed ones

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--assigned-to` | `INTEGER` | `-` | Filter by assigned user ID |
| `--assigned-to-team` | `INTEGER` | `-` | Filter by assigned team ID |
| `--contact` | `INTEGER` | `-` | Filter tasks linked to a Contact (by ID) |
| `--created-by` | `INTEGER` | `-` | Filter by creator user ID |
| `--format` | `CHOICE` | `json` |  |
| `--opportunity` | `INTEGER` | `-` | Filter tasks linked to an Opportunity (by ID) |
| `--page` | `INTEGER` | `-` |  |
| `--per-page` | `INTEGER` | `-` | Results per page (max 100) |
| `--project` | `INTEGER` | `-` | Filter tasks linked to a Project (by ID) |
| `--status` | `CHOICE` | `open` | Which tasks to return: open (Wealthbox's own default), completed, or all. 'all' issues two API calls and merges them — there is no single API value for both. |
| `--type` | `CHOICE` | `-` | all, parents, subtasks |
| `--updated-before` | `TEXT` | `-` |  |
| `--updated-since` | `TEXT` | `-` |  |
| `--verbose` / `-v` | `BOOLEAN` | `false` | Show all fields |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

**Choices for `--status`:**

- `all`
- `completed`
- `open`

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
| `--custom-field` | `TEXT` | `-` | Set a custom field as NAME=VALUE (repeatable). Name or numeric ID; see: wbox categories custom-fields --document-type Task |
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

# Everything, open and completed, for one contact
wbox tasks list --contact 12345 --status all --format table

# Mark a task complete
wbox tasks update 111 --complete
```
