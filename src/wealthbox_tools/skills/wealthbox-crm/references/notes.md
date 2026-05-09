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

## Generated Flag Reference

The following section is auto-generated from the Typer command tree by
`wbox internals regen-skill-refs`. Do not hand-edit between the markers —
edits will be overwritten on the next regen pass.

<!-- auto-gen:flags -->
### `wbox notes add`

Create a new note.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--contact` | `INTEGER` | `-` | Link to a Contact by ID |
| `--format` | `CHOICE` | `json` |  |
| `--opportunity` | `INTEGER` | `-` | Link to an Opportunity by ID |
| `--project` | `INTEGER` | `-` | Link to a Project by ID |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

### `wbox notes get`

Get a single note by ID.

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

### `wbox notes list`

List notes. Can filter by linked resource and/or updated date range.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--contact` | `INTEGER` | `-` | Filter notes linked to a Contact (by ID) |
| `--format` | `CHOICE` | `json` |  |
| `--order` | `CHOICE` | `updated` | Sort order: updated or created |
| `--page` | `INTEGER` | `-` |  |
| `--per-page` | `INTEGER` | `-` | Results per page (max 100) |
| `--updated-before` | `TEXT` | `-` |  |
| `--updated-since` | `TEXT` | `-` |  |
| `--verbose` / `-v` | `BOOLEAN` | `false` | Show all fields; content is not truncated |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

**Choices for `--order`:**

- `asc`
- `created`
- `updated`

### `wbox notes update`

Update an existing note. Note: the API does not support deleting notes.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--contact` | `INTEGER` | `-` | Replace linked Contact (by ID) |
| `--content` | `TEXT` | `-` | New note body text |
| `--format` | `CHOICE` | `json` |  |
| `--opportunity` | `INTEGER` | `-` | Replace linked Opportunity (by ID) |
| `--project` | `INTEGER` | `-` | Replace linked Project (by ID) |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`
<!-- /auto-gen:flags -->

## Examples

```bash
# Add a meeting note to a contact
wbox notes add "Discussed retirement goals. Target date 2030. Prefers conservative allocation." --contact 12345

# List recent notes for a contact
wbox notes list --contact 12345 --format table
```
