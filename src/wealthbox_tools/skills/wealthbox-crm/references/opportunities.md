# Opportunities

Track potential revenue — fees, AUM, commissions. Linked to contacts and projects.

## List Opportunities

```bash
wbox opportunities list [OPTIONS]
```

| Flag | Type | Description |
|------|------|-------------|
| `--resource-id` | INT | Filter by linked resource ID |
| `--resource-type` | Contact\|Project | Type of linked resource |
| `--order` | asc\|desc\|recent\|created | Sort order |
| `--include-closed` / `--no-include-closed` | flag | Include closed opportunities |
| `--updated-since` | ISO datetime | Modified after |
| `--updated-before` | ISO datetime | Modified before |
| `--page` | INT | Page number |
| `--per-page` | INT | Results per page |
| `--verbose`, `-v` | flag | Show all fields |
| `--format` | json\|table\|csv\|tsv | Output format |

## Get Opportunity

```bash
wbox opportunities <ID>
wbox opportunities get <ID>
```

Supports `--no-comments`, `--format`.

## Create Opportunity

```bash
wbox opportunities add <NAME> [OPTIONS]
```

| Flag | Type | Description |
|------|------|-------------|
| `<NAME>` | positional | Opportunity name (required) |
| `--target-close` | YYYY-MM-DD | Target close date (required) |
| `--probability` | INT | 0-100 (required) |
| `--stage` | INT | Stage ID (required) |
| `--description` | STR | Description |
| `--manager` | INT | Manager user ID |
| `--visible-to` | STR | Visibility |
| `--contact` | INT | Link to contact |
| `--project` | INT | Link to project |
| `--fee` | FLOAT | Fee amount |
| `--commission` | FLOAT | Commission amount |
| `--aum` | FLOAT | AUM amount |
| `--other-amount` | FLOAT | Other amount |
| `--currency` | STR | Currency code (default: USD) |
| `--more-fields` | JSON | Additional fields |
| `--format` | json\|table\|csv\|tsv | Output format |

**Note:** Use `wbox categories opportunity-stages` and `wbox categories opportunity-pipelines` to find valid stage IDs.

## Update Opportunity

```bash
wbox opportunities update <ID> [OPTIONS]
```

All create flags available. Only pass changed fields.

## Delete Opportunity

```bash
wbox opportunities delete <ID>
```

## Generated Flag Reference

The following section is auto-generated from the Typer command tree by
`wbox internals regen-skill-refs`. Do not hand-edit between the markers —
edits will be overwritten on the next regen pass.

<!-- auto-gen:flags -->
### `wbox opportunities add`

Create a new opportunity.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--aum` | `FLOAT` | `-` | AUM amount |
| `--commission` | `FLOAT` | `-` | Commission amount |
| `--contact` | `INTEGER` | `-` | Link to a Contact by ID |
| `--currency` | `TEXT` | `USD` | Currency code for all amounts (default: USD) |
| `--description` | `TEXT` | `-` |  |
| `--fee` | `FLOAT` | `-` | Fee amount |
| `--format` | `CHOICE` | `json` |  |
| `--manager` | `INTEGER` | `-` | Assign a manager by user ID |
| `--more-fields` | `TEXT` | `-` | JSON object for additional fields (e.g. custom_fields) |
| `--other-amount` | `FLOAT` | `-` | Other amount |
| `--probability` | `INTEGER` | `-` | Close probability 0–100 |
| `--project` | `INTEGER` | `-` | Link to a Project by ID |
| `--stage` | `INTEGER` | `-` | Stage ID — see: wbox categories |
| `--target-close` | `TEXT` | `-` | Target close date (e.g. 2026-06-30) |
| `--visible-to` | `TEXT` | `-` |  |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

### `wbox opportunities delete`

Delete an opportunity by ID.

_No flags._

### `wbox opportunities get`

Get a single opportunity by ID.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--format` | `CHOICE` | `json` |  |
| `--no-comments` | `BOOLEAN` | `false` | Omit comments from output |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

### `wbox opportunities list`

List opportunities with optional filters.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--format` | `CHOICE` | `json` |  |
| `--include-closed` / `--no-include-closed` | `BOOLEAN` | `-` | Include closed opportunities |
| `--order` | `CHOICE` | `-` | Sort order: asc, desc, recent, created |
| `--page` | `INTEGER` | `-` |  |
| `--per-page` | `INTEGER` | `-` | Results per page (max 100) |
| `--resource-id` | `INTEGER` | `-` | Filter by linked resource ID (requires --resource-type) |
| `--resource-type` | `CHOICE` | `-` | Filter by linked resource type: Contact, Project |
| `--updated-before` | `TEXT` | `-` |  |
| `--updated-since` | `TEXT` | `-` |  |
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
- `Project`

### `wbox opportunities update`

Update an existing opportunity. Pass only the fields you want to change.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--aum` | `FLOAT` | `-` | AUM amount |
| `--commission` | `FLOAT` | `-` | Commission amount |
| `--contact` | `INTEGER` | `-` | Replace linked Contact (by ID) |
| `--currency` | `TEXT` | `USD` | Currency code for all amounts (default: USD) |
| `--description` | `TEXT` | `-` |  |
| `--fee` | `FLOAT` | `-` | Fee amount |
| `--format` | `CHOICE` | `json` |  |
| `--manager` | `INTEGER` | `-` |  |
| `--more-fields` | `TEXT` | `-` | JSON object for additional fields (e.g. custom_fields) |
| `--name` | `TEXT` | `-` |  |
| `--other-amount` | `FLOAT` | `-` | Other amount |
| `--probability` | `INTEGER` | `-` | Close probability 0–100 |
| `--project` | `INTEGER` | `-` | Replace linked Project (by ID) |
| `--stage` | `INTEGER` | `-` | Stage ID — see: wbox categories |
| `--target-close` | `TEXT` | `-` |  |
| `--visible-to` | `TEXT` | `-` |  |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`
<!-- /auto-gen:flags -->

## Examples

```bash
# Create opportunity linked to a prospect
wbox opportunities add "Smith Retirement Plan" \
  --target-close 2026-06-30 \
  --probability 60 \
  --stage 12345 \
  --aum 500000 \
  --contact 67890

# List open opportunities
wbox opportunities list --format table
```
