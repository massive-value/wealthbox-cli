# wbox CLI Reference

The `wbox` command provides direct terminal access to the Wealthbox CRM API.

## Setup

```bash
source venv/Scripts/activate
pip install -e .
```

Set your token in `.env` at the project root:
```
WEALTHBOX_TOKEN=your_token_here
```

---

## Global Behavior

- **Output**: All commands output JSON by default. Pass `--format table` on list/get commands for tabular output.
- **Auth**: Token loaded from `WEALTHBOX_TOKEN` env var or `.env` file automatically. Override per-command with `--token`.
- **create / update commands**: Accept a single JSON string argument containing the fields. This keeps the interface stable regardless of how many fields a resource has.
- **list commands**: Accept `--option` flags for filters. All filters are optional.
- **Exit codes**: `0` on success, `1` on validation error or API error (error message printed to stderr).

---

## Command Reference

### `wbox me`

Get the current authenticated user.

```bash
wbox me
```

**Example output:**
```json
{
  "id": 70416,
  "name": "Kadin Bullock",
  "email": "kadinb@squire.com",
  "current_user": { "id": 152760, "account": 31965 },
  "accounts": [{ "id": 31965, "name": "Squire wealth advisors" }]
}
```

---

### `wbox users`

List all users in the account.

```bash
wbox users [--page INT] [--per-page INT]
```

---

### `wbox activity`

List the account activity feed.

```bash
wbox activity [OPTIONS]

Options:
  --contact INT         Filter by contact ID
  --type TEXT           Activity type filter
  --cursor TEXT         Cursor for cursor-based pagination
  --page INT
  --per-page INT
  --updated-since TEXT
  --updated-before TEXT
```

**Example:**
```bash
wbox activity --contact 30776890
wbox activity --updated-since "2025-01-01"
```

---

### `wbox comments`

List comments on a record. At least one filter is required.

```bash
wbox comments [OPTIONS]

Options:
  --resource-id INT       ID of the record (required with --resource-type)
  --resource-type TEXT    Type: Contact, Opportunity, Note, Task, Event, Project
  --updated-since TEXT
  --updated-before TEXT
```

**Example:**
```bash
wbox comments --resource-id 30776890 --resource-type Contact
```

---

### `wbox custom-fields`

List custom field definitions for your account.

```bash
wbox custom-fields [--document-type TEXT]
```

| `--document-type` values |
|--------------------------|
| `Contact` |
| `Opportunity` |
| `Project` |
| `Task` |
| `Event` |
| `ManualInvestmentAccount` |
| `DataFile` |

**Example:**
```bash
wbox custom-fields --document-type Contact
```

---

### `wbox households`

```
wbox households add-member     Add a contact to a household
wbox households remove-member  Remove a contact from a household
```

#### `wbox households add-member`

```bash
wbox households add-member <HOUSEHOLD_ID> --member-id <CONTACT_ID> [--title TEXT]
```

Examples:
```bash
wbox households add-member 30776510 --member-id 30778028 --title "Spouse"
wbox households add-member 30776510 --member-id 30778787 --title "Head"
```

#### `wbox households remove-member`

```bash
wbox households remove-member <HOUSEHOLD_ID> <CONTACT_ID>
```

Example:
```bash
wbox households remove-member 30776510 30778028
```

---

### `wbox contacts`

```
wbox contacts list     List contacts with optional filters
wbox contacts get      Get a single contact by ID
wbox contacts create   Create a new contact
wbox contacts update   Update an existing contact
wbox contacts delete   Delete a contact
```

#### `wbox contacts list`

```bash
wbox contacts list [OPTIONS]

Options:
  --name TEXT
  --contact-type TEXT      Client, Past Client, Prospect, Vendor, Organization
  --type TEXT              Person, Household, Organization, Trust
  --email TEXT
  --phone TEXT
  --tags TEXT              Comma-separated list of tags
  --active BOOL
  --order TEXT             asc, desc, recent, created, updated
  --page INT
  --per-page INT
  --updated-since TEXT
  --updated-before TEXT
  --format TEXT            json (default) or table
```

**Order:**
`asc` - Name Ascending
`desc` - Name Descending 
`recent` - Recently Viewed/Interacted with - Descending DateTime
`created` - Date Contact Created - Descending DateTime
`updated` - Date Last Modified - Descending DateTime

**Examples:**
```bash
wbox contacts list
wbox contacts list --name "Smith"
wbox contacts list --contact-type "Client" --per-page 50
wbox contacts list --type "Person" --tags "VIP,Active"
wbox contacts list --updated-since "2025-01-01" --page 2
```

#### `wbox contacts get`

```bash
wbox contacts get <CONTACT_ID>
```

#### `wbox contacts create`

```bash
wbox contacts create '<JSON>'
```

**Required fields:** at least one field must be provided.

**JSON field reference:**

| Field | Type | Enum / Notes |
|-------|------|--------------|
| `type` | string | `Person`, `Household`, `Organization`, `Trust` |
| `contact_type` | string | `Client`, `Prospect`, `Lead`, `401(k) Participant`, `Center of Influence`, `Flourish Only`, `External (Non-Client)` |
| `first_name` | string | |
| `last_name` | string | |
| `name` | string | Use for organizations/households |
| `prefix` | string | Mr., Ms., Dr., etc. |
| `suffix` | string | Jr., III, etc. |
| `gender` | string | `Female`, `Male`, `Non-binary`, `Unknown` |
| `marital_status` | string | `Married`, `Single`, `Divorced`, `Widowed`, `Life Partner`, `Separated`, `Unknown` |
| `birth_date` | string | Date string |
| `company_name` | string | |
| `job_title` | string | |
| `contact_source` | string | `Client Referral`, `Squire Referral`, `Friend/Family of Advisor`, `COI Referral`, `Conference`, `Call In`, `Website`, `Other Digital Media`, `Events/Seminars`, `Merger/Acquisition`, `Lead Gen Service`, `Person or Spouse is an Employee` |
| `status` | string | Account-defined (e.g., `Active`, `Inactive`) |
| `visible_to` | string | `Everyone`, `Only Me`, or team name |
| `assigned_to` | integer | User ID |
| `background_info` | string | |
| `important_information` | string | |
| `tags` | array of strings | |
| `email_addresses` | array | See nested object format below |
| `phone_numbers` | array | See nested object format below |
| `street_addresses` | array | See nested object format below |

**Nested object formats:**

```json
// email_addresses
{"address": "jane@example.com", "kind": "Work", "principal": true}

// phone_numbers
{"address": "555-1234", "kind": "Mobile", "extension": "101", "principal": true}

// street_addresses
{
  "kind": "Home",
  "street_line_1": "123 Main St",
  "street_line_2": "Apt 4B",
  "city": "Salt Lake City",
  "state": "UT",
  "zip_code": "84101",
  "country": "US",
  "principal": true
}
```

To **update** an existing nested record, include its `id`. To **delete** one, add `"destroy": true`.

**Examples:**
```bash
# Person with email
wbox contacts create '{"first_name": "Jane", "last_name": "Doe", "type": "Person", "contact_type": "Prospect", "email_addresses": [{"address": "jane@example.com", "kind": "Work", "principal": true}]}'

# Organization
wbox contacts create '{"name": "Acme Corp", "type": "Organization", "contact_type": "Vendor"}'

# Full person
wbox contacts create '{"first_name": "John", "last_name": "Smith", "type": "Person", "contact_type": "Client", "gender": "Male", "marital_status": "Married", "contact_source": "Referral", "phone_numbers": [{"address": "801-555-0100", "kind": "Mobile"}]}'
```

#### `wbox contacts update`

```bash
wbox contacts update <CONTACT_ID> '<JSON>'
```

Pass only the fields you want to change. At least one field required.

```bash
wbox contacts update 12345 '{"contact_type": "Client"}'
wbox contacts update 12345 '{"tags": ["VIP", "Active"]}'

# Delete an existing email (get its ID from wbox contacts get first)
wbox contacts update 12345 '{"email_addresses": [{"id": 999, "destroy": true}]}'
```

**Update semantics discovered in live testing:**
- Some fields clear more reliably with empty string `""` than with `null` (e.g., `job_title`).
- `important_information` is writable via update payloads.
- `contact_source` may be sticky when baseline is `null` on some records/accounts; test carefully before bulk updates.

#### `wbox contacts delete`

```bash
wbox contacts delete <CONTACT_ID>
```

---

### `wbox tasks`

```
wbox tasks list     List tasks with optional filters
wbox tasks get      Get a single task by ID
wbox tasks create   Create a new task
wbox tasks update   Update an existing task
wbox tasks delete   Delete a task
```

#### `wbox tasks list`

```bash
wbox tasks list [OPTIONS]

Options:
  --title TEXT
  --assigned-to-user-id INT
  --assigned-to-team-id INT
  --category-id INT
  --completed BOOL
  --due-date TEXT
  --page INT
  --per-page INT
  --updated-since TEXT
  --updated-before TEXT
```

#### `wbox tasks create`

**Required fields:** `title`, `due_date`

| Field | Type | Notes |
|-------|------|-------|
| `title` | string | Required, non-empty |
| `due_date` | string | Required, non-empty (date/datetime string) |
| `frame` | string | `today`, `tomorrow`, `this_week`, `next_week`, `future`, `specific` |
| `description` | string | |
| `assigned_to_user_id` | integer | Mutually exclusive with `assigned_to_team_id` |
| `assigned_to_team_id` | integer | Mutually exclusive with `assigned_to_user_id` |
| `category_id` | integer | |

```bash
wbox tasks create '{"title": "Call John Smith", "due_date": "2025-03-15", "frame": "specific"}'
wbox tasks create '{"title": "Send quarterly report", "due_date": "2025-03-31", "assigned_to_user_id": 152760, "category_id": 180029}'
```

#### `wbox tasks update`

```bash
wbox tasks update <TASK_ID> '<JSON>'
```

All same fields as create, plus `completed: bool`.

```bash
wbox tasks update 67890 '{"completed": true}'
wbox tasks update 67890 '{"due_date": "2025-04-01", "frame": "specific"}'
```

---

### `wbox events`

```
wbox events list
wbox events get
wbox events create
wbox events update
wbox events delete
```

#### `wbox events list`

```bash
wbox events list [OPTIONS]

Options:
  --title TEXT
  --category-id INT
  --starts-after TEXT    ISO datetime
  --starts-before TEXT   ISO datetime
  --ends-after TEXT
  --ends-before TEXT
  --page INT
  --per-page INT
  --updated-since TEXT
  --updated-before TEXT
```

#### `wbox events create`

**Required fields:** `title`, `starts_at`

Datetime format: ISO 8601 — `"2025-03-15T10:00:00-07:00"` or `"2025-03-15T17:00:00Z"`

| Field | Type | Notes |
|-------|------|-------|
| `title` | string | Required, non-empty |
| `starts_at` | string | Required, ISO 8601 datetime |
| `ends_at` | string | ISO 8601 datetime |
| `description` | string | |
| `location` | string | |
| `category_id` | integer | |

```bash
wbox events create '{"title": "Annual Review - Jane Doe", "starts_at": "2025-03-20T10:00:00-07:00", "ends_at": "2025-03-20T11:00:00-07:00"}'
wbox events create '{"title": "Team Meeting", "starts_at": "2025-03-25T14:00:00-07:00", "location": "Conference Room A"}'
```

#### `wbox events update`

```bash
wbox events update <EVENT_ID> '<JSON>'
```

---

### `wbox opportunities`

```
wbox opportunities list
wbox opportunities get
wbox opportunities create
wbox opportunities update
wbox opportunities delete
```

#### `wbox opportunities list`

```bash
wbox opportunities list [OPTIONS]

Options:
  --name TEXT
  --pipeline-id INT
  --stage-id INT
  --amount-min FLOAT
  --amount-max FLOAT
  --close-after TEXT
  --close-before TEXT
  --page INT
  --per-page INT
  --updated-since TEXT
  --updated-before TEXT
```

#### `wbox opportunities create`

**Required fields:** `name`

> `pipeline_id` and `stage_id` must always be provided together or not at all.

| Field | Type | Notes |
|-------|------|-------|
| `name` | string | Required, non-empty |
| `description` | string | |
| `pipeline_id` | integer | Must pair with `stage_id` |
| `stage_id` | integer | Must pair with `pipeline_id` |
| `amount` | float | |
| `close_date` | string | Date string (`"2025-06-30"`) |
| `primary_contact_id` | integer | Links to a contact record |

```bash
wbox opportunities create '{"name": "Smith Investment Portfolio"}'
wbox opportunities create '{"name": "Doe Retirement", "amount": 250000, "pipeline_id": 5, "stage_id": 12, "close_date": "2025-06-30", "primary_contact_id": 30776890}'
```

#### `wbox opportunities update`

```bash
wbox opportunities update <OPPORTUNITY_ID> '<JSON>'
```

> When updating the pipeline or stage, you must include both `pipeline_id` and `stage_id` together.

```bash
wbox opportunities update 22222 '{"amount": 300000}'
wbox opportunities update 22222 '{"pipeline_id": 5, "stage_id": 15}'
```

---

### `wbox notes`

> Notes cannot be deleted via the Wealthbox API.

```
wbox notes list
wbox notes get
wbox notes create
wbox notes update
```

#### `wbox notes list`

```bash
wbox notes list [--page INT] [--per-page INT] [--updated-since TEXT] [--updated-before TEXT]
```

#### Date Format for Updated Since and Updated Before
```
  "2025-01-01 01:00 PM -0700"
```

#### `wbox notes create`

**Required fields:** `content`

| Field | Type | Notes |
|-------|------|-------|
| `content` | string | Required, non-empty |
| `linked_to` | array | Array of `{"id": int, "type": str}` |

Valid `linked_to` types: `Contact`, `Opportunity`, `Project`, `Task`, `Event`, `ManualInvestmentAccount`, `DataFile`

```bash
# Standalone note
wbox notes create '{"content": "Called client, left voicemail."}'

# Linked to a contact
wbox notes create '{"content": "Discussed Q1 review.", "linked_to": [{"id": 30776890, "type": "Contact"}]}'

# Linked to multiple records
wbox notes create '{"content": "Follow-up needed.", "linked_to": [{"id": 30776890, "type": "Contact"}, {"id": 22222, "type": "Opportunity"}]}'
```

#### `wbox notes update`

```bash
wbox notes update <NOTE_ID> '{"content": "Updated note content."}'
```

---

## Common Workflows

### Find a contact then log a note

```bash
# 1. Find the contact
wbox contacts list --name "John Smith"

# 2. Note the contact ID from results, create a note
wbox notes create '{"content": "Called John, discussed rebalancing.", "linked_to": [{"id": 12345, "type": "Contact"}]}'
```

### Create a follow-up task assigned to a user

```bash
# 1. Find user IDs
wbox users

# 2. Create the task
wbox tasks create '{"title": "Follow up with Jane Doe", "due_date": "2025-03-20", "frame": "specific", "assigned_to_user_id": 152760}'
```

### Move an opportunity to a new pipeline stage

```bash
# 1. Check current state
wbox opportunities get 22222

# 2. Update both pipeline_id and stage_id together
wbox opportunities update 22222 '{"pipeline_id": 5, "stage_id": 16}'
```

### Bulk-review recent activity for a contact

```bash
wbox contacts list --name "Jane Doe"
wbox activity --contact 12345
wbox notes list --updated-since "2025-01-01"
wbox comments --resource-id 12345 --resource-type Contact
```

### Discover custom fields before setting them

```bash
wbox custom-fields --document-type Contact
# note the field "name" values from output
wbox contacts update 12345 '{"custom_fields": [{"name": "SSN", "value": "XXX-XX-1234"}]}'
```

---

## Error Reference

| Exit Code | Cause |
|-----------|-------|
| `0` | Success |
| `1` | Validation error (invalid field value, missing required field, constraint violation) |
| `1` | API error (401 bad token, 404 not found, 422 rejected payload, 5xx server error) |

Errors print to stderr. The JSON response body from the API is included in API errors.
