# Notes

Notes attach free-text content to contacts, projects, or opportunities. No delete support in the API. Text-only — file attachments must be added via the Wealthbox web UI.

## List Notes

```bash
wbox notes list [OPTIONS]
```

| Flag | Type | Description |
|------|------|-------------|
| `--contact` | INT | Filter by linked contact ID |
| `--order` | updated\|created | Sort order (default: updated) |
| `--updated-since` | ISO datetime | Modified after |
| `--updated-before` | ISO datetime | Modified before |
| `--page` | INT | Page number |
| `--per-page` | INT | Results per page |
| `--verbose`, `-v` | flag | Show all fields; don't truncate content |
| `--format` | json\|table\|csv\|tsv | Output format |

## Get Note

```bash
wbox notes <ID>
wbox notes get <ID>
```

Supports `--no-comments`, `--verbose`, `--format`.

## Create Note

```bash
wbox notes add <CONTENT> [OPTIONS]
```

| Flag | Type | Description |
|------|------|-------------|
| `<CONTENT>` | positional | Note content (required) |
| `--contact` | INT | Link to contact |
| `--project` | INT | Link to project |
| `--opportunity` | INT | Link to opportunity |
| `--format` | json\|table\|csv\|tsv | Output format |

## Update Note

```bash
wbox notes update <ID> [OPTIONS]
```

| Flag | Type | Description |
|------|------|-------------|
| `--content` | STR | New content |
| `--contact` | INT | Relink to contact |
| `--project` | INT | Relink to project |
| `--opportunity` | INT | Relink to opportunity |
| `--format` | json\|table\|csv\|tsv | Output format |

## Examples

```bash
# Add a meeting note to a contact
wbox notes add "Discussed retirement goals. Target date 2030. Prefers conservative allocation." --contact 12345

# List recent notes for a contact
wbox notes list --contact 12345 --format table
```
