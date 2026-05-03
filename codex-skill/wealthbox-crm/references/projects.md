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

## Examples

```bash
# Create a project for a client onboarding
wbox projects add "Smith Onboarding" --description "New client onboarding for John Smith"

# List all projects
wbox projects list --format table
```
