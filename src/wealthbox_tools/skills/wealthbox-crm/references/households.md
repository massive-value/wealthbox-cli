# Households

Manage membership of household contacts. Household contacts are created via `wbox contacts add household`.

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

## Examples

```bash
# Create a household, then add members
wbox contacts add household --name "The Smith Family"
# Returns ID 100

wbox households add-member 100 201 --title Head
wbox households add-member 100 202 --title Spouse
wbox households add-member 100 203 --title Dependent
```
