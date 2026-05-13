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
| `--assigned-to` | INT | User ID (fetches all pages, client-side filter). Get yours via `wbox me user-id`, **not** `wbox me \| jq .id` (that's the login profile, which silently returns zero results). |
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

Returns the full contact record. Contacts do not carry comments in Wealthbox — to read comments, fetch the related task, note, event, opportunity, project, or workflow with its `get` command (those default to including comments and accept `--no-comments` to suppress).

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
| `--tags` | STR | Comma-separated tag names (e.g. "VIP,Q1-Outreach"). New tags are auto-created. |
| `--more-fields` | JSON | Additional fields as JSON object |
| `--format` | json\|table\|csv\|tsv | Output format |

### Household
```bash
wbox contacts add household --name <NAME> [OPTIONS]
```
`--name` is required. Supports: `--contact-type`, `--contact-source`, `--active/--inactive`, `--assigned-to`, `--email`, `--email-type`, `--tags`, `--more-fields`, `--format`.

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
| `--tags` | STR | Comma-separated tag names. Replaces all tags — include existing ones to keep. |
| `--json` | STR | Full JSON for nested/complex fields |
| `--format` | json\|table\|csv\|tsv | Output format |

## Delete Contact

```bash
wbox contacts delete <ID>
```
No output on success.

## Contact Categories

Each of these is also available at the workspace level via `wbox categories <name>` — both forms return the same data.

```bash
wbox contacts categories contact-types
wbox contacts categories contact-sources
wbox contacts categories email-types
wbox contacts categories phone-types
wbox contacts categories address-types
wbox contacts categories website-types
wbox contacts categories contact-roles
```

## Generated Flag Reference

The following section is auto-generated from the Typer command tree by
`wbox internals regen-skill-refs`. Do not hand-edit between the markers —
edits will be overwritten on the next regen pass.

<!-- auto-gen:flags -->
### `wbox contacts add household`

Create a Household contact.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--active` / `--inactive` | `BOOLEAN` | `-` | Set contact status to Active or Inactive |
| `--assigned-to` | `INTEGER` | `-` | Assign to a user by ID |
| `--contact-source` | `TEXT` | `-` |  |
| `--contact-type` | `TEXT` | `-` | e.g. Client, Prospect |
| `--email` | `TEXT` | `-` | Primary email address |
| `--email-type` | `TEXT` | `-` | Email kind (e.g. Work, Personal) — see: wbox contacts categories email-types |
| `--format` | `CHOICE` | `json` |  |
| `--more-fields` | `TEXT` | `-` | Extra fields as JSON object (merged with flags; cannot override explicit flags) |
| `--name` | `TEXT` | `-` | Household name (required) |
| `--tags` | `TEXT` | `-` | Comma-separated tag names (e.g. 'VIP,Q1-Outreach'). New tags are auto-created. |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

### `wbox contacts add org`

Create an Organization contact.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--active` / `--inactive` | `BOOLEAN` | `-` | Set contact status to Active or Inactive |
| `--assigned-to` | `INTEGER` | `-` | Assign to a user by ID |
| `--contact-source` | `TEXT` | `-` |  |
| `--contact-type` | `TEXT` | `-` | e.g. Client, Prospect |
| `--email` | `TEXT` | `-` | Primary email address |
| `--email-type` | `TEXT` | `-` | Email kind (e.g. Work, Personal) — see: wbox contacts categories email-types |
| `--format` | `CHOICE` | `json` |  |
| `--more-fields` | `TEXT` | `-` | Extra fields as JSON object (merged with flags; cannot override explicit flags) |
| `--name` | `TEXT` | `-` | Organization name (required) |
| `--phone` | `TEXT` | `-` | Primary phone number |
| `--phone-type` | `TEXT` | `-` | Phone kind (e.g. Work, Mobile) — see: wbox contacts categories phone-types |
| `--tags` | `TEXT` | `-` | Comma-separated tag names (e.g. 'VIP,Q1-Outreach'). New tags are auto-created. |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

### `wbox contacts add person`

Create a Person contact.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--active` / `--inactive` | `BOOLEAN` | `-` | Set contact status to Active or Inactive |
| `--anniversary` | `TEXT` | `-` | Format: YYYY-MM-DD |
| `--assigned-to` | `INTEGER` | `-` | Assign to a user by ID |
| `--birth-date` | `TEXT` | `-` | Format: YYYY-MM-DD |
| `--company-name` | `TEXT` | `-` |  |
| `--contact-source` | `TEXT` | `-` |  |
| `--contact-type` | `TEXT` | `-` | e.g. Client, Prospect |
| `--email` | `TEXT` | `-` | Primary email address |
| `--email-type` | `TEXT` | `-` | Email kind (e.g. Work, Personal) — see: wbox contacts categories email-types |
| `--first-name` | `TEXT` | `-` |  |
| `--format` | `CHOICE` | `json` |  |
| `--gender` | `CHOICE` | `-` |  |
| `--job-title` | `TEXT` | `-` |  |
| `--last-name` | `TEXT` | `-` |  |
| `--marital-status` | `CHOICE` | `-` |  |
| `--middle-name` | `TEXT` | `-` |  |
| `--more-fields` | `TEXT` | `-` | Extra fields as JSON object (merged with flags; cannot override explicit flags) |
| `--nickname` | `TEXT` | `-` |  |
| `--phone` | `TEXT` | `-` | Primary phone number |
| `--phone-type` | `TEXT` | `-` | Phone kind (e.g. Work, Mobile) — see: wbox contacts categories phone-types |
| `--prefix` | `TEXT` | `-` |  |
| `--suffix` | `TEXT` | `-` |  |
| `--tags` | `TEXT` | `-` | Comma-separated tag names (e.g. 'VIP,Q1-Outreach'). New tags are auto-created. |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

**Choices for `--gender`:**

- `Female`
- `Male`
- `Non-binary`
- `Unknown`

**Choices for `--marital-status`:**

- `Divorced`
- `Life partner`
- `Married`
- `Separated`
- `Single`
- `Unknown`
- `Widowed`

### `wbox contacts add trust`

Create a Trust contact.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--active` / `--inactive` | `BOOLEAN` | `-` | Set contact status to Active or Inactive |
| `--assigned-to` | `INTEGER` | `-` | Assign to a user by ID |
| `--contact-source` | `TEXT` | `-` |  |
| `--contact-type` | `TEXT` | `-` | e.g. Client, Prospect |
| `--email` | `TEXT` | `-` | Primary email address |
| `--email-type` | `TEXT` | `-` | Email kind (e.g. Work, Personal) — see: wbox contacts categories email-types |
| `--format` | `CHOICE` | `json` |  |
| `--more-fields` | `TEXT` | `-` | Extra fields as JSON object (merged with flags; cannot override explicit flags) |
| `--name` | `TEXT` | `-` | Trust name (required) |
| `--phone` | `TEXT` | `-` | Primary phone number |
| `--phone-type` | `TEXT` | `-` | Phone kind (e.g. Work, Mobile) — see: wbox contacts categories phone-types |
| `--tags` | `TEXT` | `-` | Comma-separated tag names (e.g. 'VIP,Q1-Outreach'). New tags are auto-created. |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

### `wbox contacts categories address-types`

List address type options.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--format` | `CHOICE` | `json` |  |
| `--page` | `INTEGER` | `-` | Page number |
| `--per-page` | `INTEGER` | `-` | Results per page (max 100) |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

### `wbox contacts categories contact-roles`

List contact role options.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--format` | `CHOICE` | `json` |  |
| `--page` | `INTEGER` | `-` | Page number |
| `--per-page` | `INTEGER` | `-` | Results per page (max 100) |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

### `wbox contacts categories contact-sources`

List contact source options.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--format` | `CHOICE` | `json` |  |
| `--page` | `INTEGER` | `-` | Page number |
| `--per-page` | `INTEGER` | `-` | Results per page (max 100) |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

### `wbox contacts categories contact-types`

List contact type options.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--format` | `CHOICE` | `json` |  |
| `--page` | `INTEGER` | `-` | Page number |
| `--per-page` | `INTEGER` | `-` | Results per page (max 100) |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

### `wbox contacts categories email-types`

List email type options.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--format` | `CHOICE` | `json` |  |
| `--page` | `INTEGER` | `-` | Page number |
| `--per-page` | `INTEGER` | `-` | Results per page (max 100) |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

### `wbox contacts categories phone-types`

List phone type options.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--format` | `CHOICE` | `json` |  |
| `--page` | `INTEGER` | `-` | Page number |
| `--per-page` | `INTEGER` | `-` | Results per page (max 100) |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

### `wbox contacts categories website-types`

List website type options.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--format` | `CHOICE` | `json` |  |
| `--page` | `INTEGER` | `-` | Page number |
| `--per-page` | `INTEGER` | `-` | Results per page (max 100) |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

### `wbox contacts delete`

Delete an existing contact.

_No flags._

### `wbox contacts get`

Get a single contact by ID.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--format` | `CHOICE` | `json` |  |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

### `wbox contacts list`

List contacts with optional filters.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--active` / `--inactive` | `BOOLEAN` | `-` | Filter by active status |
| `--assigned-to` | `INTEGER` | `-` | Filter by assigned user ID (client-side scan — fetches all pages). |
| `--contact-type` | `TEXT` | `-` | Client, Prospect, Vendor, etc. - see wbox contacts categories contact-types |
| `--deleted` | `BOOLEAN` | `-` | Filter to deleted contacts only (omit to see non-deleted, which is the API default) |
| `--deleted-since` | `TEXT` | `-` | Only returns deleted contacts that were deleted on or after this timestamp |
| `--email` | `TEXT` | `-` | Filter by email - Full Match |
| `--format` | `CHOICE` | `json` |  |
| `--household-title` | `CHOICE` | `-` | The household title you wish to filter the household title |
| `--name` | `TEXT` | `-` | Filter by name - Contains |
| `--order` | `CHOICE` | `asc` | The order that the contacts should be returned in |
| `--page` | `INTEGER` | `-` | Page number |
| `--per-page` | `INTEGER` | `-` | Results per page (max 100) |
| `--phone` | `TEXT` | `-` | Filter by phone - Full Match - Parsing handled by Wealthbox |
| `--tags` | `TEXT` | `-` | Comma-separated tags |
| `--type` | `CHOICE` | `-` | Record Type - Person, Household, Organization, or Trust |
| `--updated-before` | `TEXT` | `-` | Format of 'YYYY-MM-DD 07:00 AM -0700' |
| `--updated-since` | `TEXT` | `-` | Format of 'YYYY-MM-DD 07:00 AM -0700' |
| `--verbose` / `-v` | `BOOLEAN` | `false` | Show all fields |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

**Choices for `--household-title`:**

- `Child`
- `Grandchild`
- `Grandparent`
- `Head`
- `Other Dependent`
- `Parent`
- `Partner`
- `Sibling`
- `Spouse`

**Choices for `--order`:**

- `asc`
- `created`
- `desc`
- `recent`
- `updated`

**Choices for `--type`:**

- `Household`
- `Organization`
- `Person`
- `Trust`

### `wbox contacts update`

Update an existing contact. Pass only the fields you want to change.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--active` / `--inactive` | `BOOLEAN` | `-` | Set contact status to Active or Inactive |
| `--assigned-to` | `INTEGER` | `-` | Reassign to a user by ID |
| `--company-name` | `TEXT` | `-` |  |
| `--contact-source` | `TEXT` | `-` |  |
| `--contact-type` | `TEXT` | `-` | e.g. Client, Prospect |
| `--first-name` | `TEXT` | `-` |  |
| `--format` | `CHOICE` | `json` |  |
| `--job-title` | `TEXT` | `-` |  |
| `--json` | `TEXT` | `-` | Full update as JSON (for nested fields like email_addresses) |
| `--last-name` | `TEXT` | `-` |  |
| `--middle-name` | `TEXT` | `-` |  |
| `--name` | `TEXT` | `-` | Full name (for Household/Org/Trust) |
| `--tags` | `TEXT` | `-` | Comma-separated tag names (e.g. 'VIP,Q1-Outreach'). Replaces all tags on the contact — include existing tags you wish to keep. New tags are auto-created. |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`
<!-- /auto-gen:flags -->

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
