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
