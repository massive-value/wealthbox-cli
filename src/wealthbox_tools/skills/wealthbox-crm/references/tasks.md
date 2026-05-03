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
| `--frame` | today\|tomorrow\|this-week\|next-week\|this-month\|next-month\|... | Relative due date (XOR with --due-date) |
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

## Update Task

```bash
wbox tasks update <ID> [OPTIONS]
```

| Flag | Type | Description |
|------|------|-------------|
| `--name` | STR | Rename |
| `--due-date` | STR | Change due date |
| `--frame` | STR | Change relative due date |
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

## Examples

```bash
# Create a follow-up task linked to a contact
wbox tasks add "Follow up with Jane" --frame next-week --priority High --contact 12345

# List my outstanding tasks
wbox tasks list --assigned-to 67890 --format table

# Mark a task complete
wbox tasks update 111 --complete
```
