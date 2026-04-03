# Contacts

Contacts are the core record in Wealthbox. Four types: Person, Household, Organization, Trust.

## List Contacts

```bash
wbox contacts list [OPTIONS]
```

| Flag | Type | Description |
|------|------|-------------|
| `--type` | Person\|Household\|Organization\|Trust | Filter by contact type |
| `--name` | STR | Filter by name (contains match) |
| `--email` | STR | Filter by email (exact match) |
| `--phone` | STR | Filter by phone (exact match) |
| `--contact-type` | STR | Category: Client, Prospect, Vendor, etc. |
| `--active` / `--inactive` | flag | Filter by active status |
| `--deleted` | flag | Show deleted contacts only |
| `--household-title` | STR | Filter by household title |
| `--tags` | STR | Comma-separated tag names |
| `--order` | asc\|desc | Sort order |
| `--assigned-to` | INT | User ID (fetches all pages, client-side filter) |
| `--updated-since` | ISO datetime | Modified after this datetime |
| `--updated-before` | ISO datetime | Modified before this datetime |
| `--deleted-since` | ISO datetime | Deleted after this datetime |
| `--page` | INT | Page number |
| `--per-page` | INT | Results per page (max 100) |
| `--verbose`, `-v` | flag | Show all fields |
| `--format` | json\|table\|csv\|tsv | Output format |

## Get Contact

```bash
wbox contacts <ID>
wbox contacts get <ID>
```

Returns full contact record including comments (use `--no-comments` to omit).

## Create Contact

Each type has its own subcommand:

### Person
```bash
wbox contacts add person [OPTIONS]
```

| Flag | Type | Description |
|------|------|-------------|
| `--first-name` | STR | First name |
| `--last-name` | STR | Last name |
| `--middle-name` | STR | Middle name |
| `--prefix` | STR | Mr., Mrs., Dr., etc. |
| `--suffix` | STR | Jr., III, etc. |
| `--nickname` | STR | Nickname |
| `--gender` | M\|F\|Other\|Prefer not to say | Gender |
| `--marital-status` | Single\|Married\|Divorced\|Widowed\|Separated\|Prefer not to say | Marital status |
| `--birth-date` | YYYY-MM-DD | Date of birth |
| `--anniversary` | YYYY-MM-DD | Anniversary date |
| `--job-title` | STR | Job title |
| `--company-name` | STR | Company name |
| `--contact-type` | STR | Category (Client, Prospect, etc.) |
| `--contact-source` | STR | How they were sourced |
| `--active` / `--inactive` | flag | Active status (default: active) |
| `--assigned-to` | INT | Assigned user ID |
| `--email` | STR | Email address |
| `--email-type` | STR | Work, Personal, etc. |
| `--phone` | STR | Phone number |
| `--phone-type` | STR | Work, Mobile, etc. |
| `--more-fields` | JSON | Additional fields as JSON object |
| `--format` | json\|table\|csv\|tsv | Output format |

### Household
```bash
wbox contacts add household --name <NAME> [OPTIONS]
```
`--name` is required. Supports: `--contact-type`, `--contact-source`, `--active/--inactive`, `--assigned-to`, `--email`, `--email-type`, `--more-fields`, `--format`.

### Organization
```bash
wbox contacts add org --name <NAME> [OPTIONS]
```
`--name` is required. Supports all household flags plus `--phone`, `--phone-type`.

### Trust
```bash
wbox contacts add trust --name <NAME> [OPTIONS]
```
Same flags as Organization.

## Update Contact

```bash
wbox contacts update <ID> [OPTIONS]
```

Only pass the fields you want to change:

| Flag | Type | Description |
|------|------|-------------|
| `--first-name` | STR | (Person only) |
| `--middle-name` | STR | (Person only) |
| `--last-name` | STR | (Person only) |
| `--name` | STR | Full name (Household/Org/Trust) |
| `--job-title` | STR | Job title |
| `--company-name` | STR | Company name |
| `--contact-type` | STR | Category |
| `--contact-source` | STR | Source |
| `--active` / `--inactive` | flag | Active status |
| `--assigned-to` | INT | Reassign to user ID |
| `--json` | STR | Full JSON for nested/complex fields |
| `--format` | json\|table\|csv\|tsv | Output format |

## Delete Contact

```bash
wbox contacts delete <ID>
```
No output on success.

## Contact Categories

```bash
wbox contacts categories contact-types
wbox contacts categories contact-sources
wbox contacts categories email-types
wbox contacts categories phone-types
wbox contacts categories address-types
wbox contacts categories website-types
wbox contacts categories contact-roles
```

## Examples

```bash
# Find all prospects named Smith
wbox contacts list --name Smith --contact-type Prospect --format table

# Create a new person
wbox contacts add person --first-name Jane --last-name Doe --contact-type Client --email jane@example.com --email-type Work

# Update job title
wbox contacts update 12345 --job-title "CFO"

# Create a household and add members (two-step)
wbox contacts add household --name "The Smith Family"
# note the returned ID, then:
wbox households add-member <HOUSEHOLD_ID> <MEMBER_ID> --title Head
```
