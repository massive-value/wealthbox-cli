# Projects

Group related work. Can be linked from tasks, notes, events, opportunities, and workflows. No delete support.

## List Projects

```bash
wbox projects list [OPTIONS]
```

| Flag | Type | Description |
|------|------|-------------|
| `--updated-since` | ISO datetime | Modified after |
| `--updated-before` | ISO datetime | Modified before |
| `--page` | INT | Page number |
| `--per-page` | INT | Results per page |
| `--verbose`, `-v` | flag | Show all fields |
| `--format` | json\|table\|csv\|tsv | Output format |

## Get Project

```bash
wbox projects <ID>
wbox projects get <ID>
```

Supports `--no-comments`, `--format`.

## Create Project

```bash
wbox projects add <NAME> [OPTIONS]
```

| Flag | Type | Description |
|------|------|-------------|
| `<NAME>` | positional | Project name (required) |
| `--description` | STR | Description (required) |
| `--organizer` | INT | Organizer user ID |
| `--visible-to` | STR | Visibility |
| `--more-fields` | JSON | Additional fields |
| `--format` | json\|table\|csv\|tsv | Output format |

## Update Project

```bash
wbox projects update <ID> [OPTIONS]
```

Flags: `--name`, `--description`, `--organizer`, `--visible-to`, `--more-fields`, `--format`.

## Generated Flag Reference

The following section is auto-generated from the Typer command tree by
`wbox internals regen-skill-refs`. Do not hand-edit between the markers —
edits will be overwritten on the next regen pass.

<!-- auto-gen:flags -->
### `wbox projects add`

Create a new project.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--description` | `TEXT` | `-` | Project description |
| `--format` | `CHOICE` | `json` |  |
| `--more-fields` | `TEXT` | `-` | JSON object for additional fields (e.g. custom_fields) |
| `--organizer` | `INTEGER` | `-` | Organizer user ID |
| `--visible-to` | `TEXT` | `-` |  |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

### `wbox projects get`

Get a single project by ID.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--format` | `CHOICE` | `json` |  |
| `--no-comments` | `BOOLEAN` | `false` | Omit comments from output |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

### `wbox projects list`

List projects with optional date range filters.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--format` | `CHOICE` | `json` |  |
| `--page` | `INTEGER` | `-` |  |
| `--per-page` | `INTEGER` | `-` | Results per page (max 100) |
| `--updated-before` | `TEXT` | `-` |  |
| `--updated-since` | `TEXT` | `-` |  |
| `--verbose` / `-v` | `BOOLEAN` | `false` | Show all fields |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

### `wbox projects update`

Update an existing project. Pass only the fields you want to change.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--description` | `TEXT` | `-` |  |
| `--format` | `CHOICE` | `json` |  |
| `--more-fields` | `TEXT` | `-` | JSON object for additional fields (e.g. custom_fields) |
| `--name` | `TEXT` | `-` |  |
| `--organizer` | `INTEGER` | `-` | Organizer user ID |
| `--visible-to` | `TEXT` | `-` |  |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`
<!-- /auto-gen:flags -->

## Examples

```bash
# Create a project for a client onboarding
wbox projects add "Smith Onboarding" --description "New client onboarding for John Smith"

# List all projects
wbox projects list --format table
```
