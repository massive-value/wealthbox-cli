# Workflows

Template-based process tracking. Created from templates, progressed by completing/reverting steps.

## List Workflows

```bash
wbox workflows list [OPTIONS]
```

| Flag | Type | Description |
|------|------|-------------|
| `--resource-id` | INT | Filter by linked resource ID |
| `--resource-type` | Contact\|Project | Type of linked resource |
| `--status` | active\|completed\|scheduled | Filter by status |
| `--updated-since` | ISO datetime | Modified after |
| `--updated-before` | ISO datetime | Modified before |
| `--page` | INT | Page number |
| `--per-page` | INT | Results per page |
| `--verbose`, `-v` | flag | Show all fields |
| `--format` | json\|table\|csv\|tsv | Output format |

## Get Workflow

```bash
wbox workflows <ID>
wbox workflows get <ID>
```

Supports `--no-comments`, `--format`.

## Create Workflow

```bash
wbox workflows add [OPTIONS]
```

| Flag | Type | Description |
|------|------|-------------|
| `--template` | INT | Workflow template ID (required) |
| `--label` | STR | Label/name for this instance |
| `--contact` | INT | Link to contact |
| `--project` | INT | Link to project |
| `--opportunity` | INT | Link to opportunity |
| `--visible-to` | STR | Visibility |
| `--starts-at` | STR | Start date |
| `--more-fields` | JSON | Additional fields |
| `--format` | json\|table\|csv\|tsv | Output format |

**Note:** Use `wbox workflows templates list` to find available template IDs.

## Complete Step

```bash
wbox workflows complete-step <WORKFLOW_ID> <STEP_ID> [OPTIONS]
```

| Flag | Type | Description |
|------|------|-------------|
| `--outcome-id` | INT | Outcome selection |
| `--due-date` | STR | For restarting a step |
| `--due-date-set` | flag | Whether restarted step has due date |
| `--format` | json\|table\|csv\|tsv | Output format |

## Revert Step

```bash
wbox workflows revert-step <WORKFLOW_ID> <STEP_ID> [OPTIONS]
```

## List Templates

```bash
wbox workflows templates list [OPTIONS]
```

Same filter flags as workflow list.

## Examples

```bash
# List available templates
wbox workflows templates list --format table

# Start onboarding workflow for a contact
wbox workflows add --template 123 --contact 67890 --label "Smith Onboarding"

# Complete a workflow step
wbox workflows complete-step 111 222
```
