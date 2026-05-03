# Lookups

Read-only resources: categories, users, activity feed, and current user info.

## Current User

```bash
wbox me [--format json|table|csv|tsv]
```

Returns info about the authenticated user. Good for verifying token setup and getting your user ID.

## Users

```bash
wbox users list [--verbose] [--format json|table|csv|tsv]
```

Lists all users in the workspace. Use to find user IDs for `--assigned-to` flags.

## Activity Feed

```bash
wbox activity list [OPTIONS]
```

| Flag | Type | Description |
|------|------|-------------|
| `--contact` | INT | Filter by contact ID |
| `--cursor` | STR | Cursor for next page (from previous response) |
| `--type` | STR | Activity type filter |
| `--updated-since` | ISO datetime | Activities after |
| `--updated-before` | ISO datetime | Activities before |
| `--verbose`, `-v` | flag | Show full body content |
| `--format` | json\|table\|csv\|tsv | Output format |

**Important:** Activity uses cursor-based pagination, NOT `--page`/`--per-page`. Use the cursor value from the previous response for the next page.

## Categories

Every category type is available under `wbox categories <name>`. The full set:

```bash
wbox categories tags
wbox categories file-categories
wbox categories opportunity-stages
wbox categories opportunity-pipelines
wbox categories investment-objectives
wbox categories financial-account-types
wbox categories contact-types
wbox categories contact-sources
wbox categories email-types
wbox categories phone-types
wbox categories address-types
wbox categories website-types
wbox categories contact-roles
wbox categories event-categories
wbox categories task-categories
wbox categories custom-fields [--document-type STR] [--page INT] [--per-page INT] [--format ...]
```

The contact-related types are also reachable as aliases under `wbox contacts categories <name>` (contact-types, contact-sources, email-types, phone-types, address-types, website-types, contact-roles). Likewise, `wbox events categories` and `wbox tasks categories` are aliases for `wbox categories event-categories` and `wbox categories task-categories`. Either form returns the same data.

## Examples

```bash
# Get your user ID
wbox me --format table

# Find a user ID for assignment
wbox users list --format table

# Check recent activity for a contact
wbox activity list --contact 12345 --format table

# Look up valid contact types
wbox categories contact-types
```
