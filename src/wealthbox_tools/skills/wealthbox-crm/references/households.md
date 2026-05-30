# Households

Manage membership of household contacts. Household contacts are created via `wbox contacts add household`.

> ⚠️ **Add members one at a time, sequentially.** Each `add-member` call
> rewrites the household's member list, so concurrent/parallel calls race and
> the last write clobbers the earlier ones. Run them in series and wait for
> each to return before issuing the next.

## Add Member

```bash
wbox households add-member <HOUSEHOLD_ID> <MEMBER_ID> [OPTIONS]
```

| Flag | Type | Description |
|------|------|-------------|
| `<HOUSEHOLD_ID>` | positional | Household contact ID (required) |
| `<MEMBER_ID>` | positional | Person contact ID to add (required) |
| `--title` | Spouse\|Head\|Dependent\|Other | Member role (required) |
| `--format` | json\|table\|csv\|tsv | Output format |

## Remove Member

```bash
wbox households remove-member <HOUSEHOLD_ID> <MEMBER_ID> [OPTIONS]
```

| Flag | Type | Description |
|------|------|-------------|
| `<HOUSEHOLD_ID>` | positional | Household contact ID (required) |
| `<MEMBER_ID>` | positional | Person contact ID to remove (required) |
| `--format` | json\|table\|csv\|tsv | Output format |

## Generated Flag Reference

The following section is auto-generated from the Typer command tree by
`wbox internals regen-skill-refs`. Do not hand-edit between the markers —
edits will be overwritten on the next regen pass.

<!-- auto-gen:flags -->
### `wbox households add-member`

Add a member to a household. Usage: add-member <household_id> <member_id> --title <title>

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--format` | `CHOICE` | `json` |  |
| `--title` | `CHOICE` | `-` | Household title for member (e.g. Spouse, Head) |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

**Choices for `--title`:**

- `Child`
- `Grandchild`
- `Grandparent`
- `Head`
- `Other Dependent`
- `Parent`
- `Partner`
- `Sibling`
- `Spouse`

### `wbox households remove-member`

Remove a member from a household.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--format` | `CHOICE` | `json` |  |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`
<!-- /auto-gen:flags -->

## Examples

```bash
# Create a household, then add members
wbox contacts add household --name "The Smith Family"
# Returns ID 100

wbox households add-member 100 201 --title Head
wbox households add-member 100 202 --title Spouse
wbox households add-member 100 203 --title Dependent
```
