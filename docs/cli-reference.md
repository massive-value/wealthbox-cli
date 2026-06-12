# CLI Command Reference

Full command reference for the `wbox` CLI. For project overview, installation, and configuration see the [Getting Started](getting-started.md) guide.

------------------------------------------------------------------------

## Basic Usage

``` bash
wbox <resource> <command> [options]
```

Health checks:

``` bash
wbox me
wbox users list
wbox activity list
```

Activity feed pagination uses cursor-based navigation (not page/per-page):

``` bash
wbox activity list --cursor <cursor_from_previous_response>
wbox activity list --verbose   # show full body content (default truncates to 500 chars)
```

------------------------------------------------------------------------

## Output Formats

All list and get commands accept `--format [json|table|csv|tsv]` (default: `json`).

``` bash
# Terminal table (bordered grid, good for interactive use)
wbox contacts list --format table
wbox contacts get 123 --format table

# CSV — pipe to a file for Excel/Sheets
wbox contacts list --format csv > contacts.csv

# TSV
wbox tasks list --format tsv > tasks.tsv
```

**Single-object commands** (e.g. `get`) render as a two-column Field/Value table.
**List commands** render as a row-per-record table and print `Showing N of M results` to stderr when a total count is available.

**Nested field flattening:** Tabular output automatically flattens nested API structures so columns stay readable:

| Field type | Raw API value | Flattened |
|---|---|---|
| `linked_to` | `[{"id": 12, "type": "Contact"}]` | `Contact:12` |
| `email_addresses` | `[{"address": "a@b.com", "principal": true, ...}]` | `a@b.com` |
| `tags` | `["VIP", "Prospect"]` | `VIP, Prospect` |
| `custom_fields` | `[{...}, {...}]` | `[2 items]` |

Use `--verbose` with tabular formats to include all fields (same as JSON verbose mode).

------------------------------------------------------------------------

## Exit Codes

`wbox` returns differentiated exit codes so scripts can branch on the failure class rather than just success/failure:

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Validation / user error — invalid input rejected by the input models, or a non-auth `4xx` from the API (e.g. `404 Not Found`, `422 Unprocessable Entity`) |
| `2` | Authentication error — API returned `401 Unauthorized` or `403 Forbidden` (e.g. a missing, invalid, or insufficiently-scoped token) |
| `3` | Server error — API returned a `5xx` status (e.g. `500`, `503`) |

Click (the underlying CLI parser) also exits with code `2` for **usage errors** — an unknown flag, a bad option value, or a missing required argument. These are raised by the parser before the command body runs, so they never reach the API. The overlap with the authentication code is pre-existing and acceptable; in practice a usage error prints a Click `Usage:` message while an auth error prints `API Error (401): ...`.

**Debugging:** set `WBOX_DEBUG=1` (any non-empty value) to print the full Python traceback to stderr in addition to the friendly one-line error. The mapped exit code is unchanged, so `WBOX_DEBUG=1` is safe to leave on in scripts that branch on exit status.

``` bash
# Linux/macOS
WBOX_DEBUG=1 wbox contacts get 999999

# PowerShell
$env:WBOX_DEBUG="1"; wbox contacts get 999999
```

------------------------------------------------------------------------

## Contacts

### List

``` bash
wbox contacts list
wbox contacts list --type Person|Household|Organization|Trust
wbox contacts list --contact-type "Client"
wbox contacts list --name "Smith"
wbox contacts list --active
wbox contacts list --tags "tag1,tag2"
wbox contacts list --updated-since "2025-01-01T00:00:00Z"
wbox contacts list --per-page 100 --page 2
```

Filter by assigned user (fetches all pages client-side — the API has no server-side filter for this):

``` bash
wbox contacts list --assigned-to <user_id>
wbox contacts list --assigned-to <user_id> --type Household
```

Progress output goes to stderr, so the result stays pipeable:

``` bash
wbox contacts list --assigned-to <user_id> | jq '.contacts | length'
```

### Add

Contact creation is type-specific via subcommands:

``` bash
wbox contacts add person --first-name "John" --last-name "Doe" --contact-type "Client"
wbox contacts add person --first-name "Jane" --email jane@example.com --email-type "Work"
wbox contacts add household --name "Smith Family" --active
wbox contacts add org --name "Acme Corp" --contact-type "Prospect"
wbox contacts add trust --name "Bullock Family Trust" --contact-type "Client"
```

Person contacts also expose person-specific flags:

``` bash
wbox contacts add person \
  --first-name "Jane" \
  --last-name "Doe" \
  --prefix "Dr." \
  --nickname "Janie" \
  --gender "Female" \
  --marital-status "Married" \
  --birth-date "1980-01-15" \
  --anniversary "2005-06-10"
```

For uncommon fields not covered by direct flags, use `--more-fields` with a JSON object. It is merged with the explicit flags but cannot override them:

``` bash
wbox contacts add person --first-name "Jane" --more-fields '{"background_information": "VIP prospect", "client_since": "2020-01-01"}'
wbox contacts add household --name "Smith Family" --more-fields '{"important_information": "Prefers email"}'
```

Use `background_information` (not `background_info`) for contact payloads.

### Get

``` bash
wbox contacts get <contact_id>
wbox contacts get <contact_id> --verbose
```

### Update

Pass only the fields you want to change:

``` bash
wbox contacts update <contact_id> --contact-type Client
wbox contacts update <contact_id> --first-name Jonathan --last-name Smith
wbox contacts update <contact_id> --inactive
wbox contacts update <contact_id> --assigned-to <user_id>
```

For nested field updates (e.g. replacing email addresses), use `--json`:

``` bash
wbox contacts update <contact_id> --json '{"email_addresses": [{"address": "new@example.com", "kind": "Work", "principal": true}]}'
```

### Delete

``` bash
wbox contacts delete <contact_id>
```

### Contact Categories

``` bash
wbox contacts categories contact-types
wbox contacts categories contact-sources
wbox contacts categories email-types
wbox contacts categories phone-types
wbox contacts categories address-types
wbox contacts categories website-types
wbox contacts categories contact-roles
```

------------------------------------------------------------------------

## Households

Add member:

``` bash
wbox households add-member <household_id> <member_id> --title "Head|Spouse|Parent|Other Dependent|Child|Sibling|Partner|Grandchild|Grandparent"
```

Remove member:

``` bash
wbox households remove-member <household_id> <member_id>
```

------------------------------------------------------------------------

## Tasks

### List

``` bash
wbox tasks list
wbox tasks list --contact <id>
wbox tasks list --project <id>
wbox tasks list --opportunity <id>
wbox tasks list --assigned-to <user_id>
wbox tasks list --include-completed
wbox tasks list --updated-since "2025-01-01T00:00:00Z"
```

### Categories

``` bash
wbox tasks categories
```

### Add

``` bash
wbox tasks add "Send proposal" --due-date "2026-03-20T09:00:00-07:00"
wbox tasks add "Follow up call" --frame tomorrow
wbox tasks add "Review documents" --due-date "2026-03-20T09:00:00-07:00" --priority High --contact <contact_id>
wbox tasks add "Team meeting" --frame today --assigned-to <user_id>
```

Use `--more-fields` for uncommon fields not covered by direct flags. It must be a JSON object and cannot shadow explicit CLI args like `name`, `due_date`, `frame`, `priority`, `assigned_to`, or resource links:

``` bash
wbox tasks add "Quarterly review" --due-date "2026-03-20T09:00:00-07:00" --more-fields '{"category": 123, "description": "Annual review meeting"}'
```

### Get

``` bash
wbox tasks get <task_id>
```

### Update

Pass only the fields you want to change:

``` bash
wbox tasks update <task_id> --name "Updated task name"
wbox tasks update <task_id> --due-date "2026-04-01T09:00:00-07:00"
wbox tasks update <task_id> --priority High
wbox tasks update <task_id> --complete
wbox tasks update <task_id> --no-complete
wbox tasks update <task_id> --contact <contact_id>
```

### Delete

``` bash
wbox tasks delete <task_id>
```

------------------------------------------------------------------------

## Events

### List

``` bash
wbox events list
wbox events list --resource-id <id> --resource-type Contact|Opportunity|Project
wbox events list --start-date-min "2026-01-01" --start-date-max "2026-12-31"
wbox events list --order asc|desc|recent|created
```

### Categories

``` bash
wbox events categories
```

### Add

``` bash
wbox events add "Annual Review" --starts-at "2026-04-01T10:00:00-07:00" --ends-at "2026-04-01T11:00:00-07:00"
wbox events add "Client Meeting" --starts-at "2026-04-01T10:00:00-07:00" --ends-at "2026-04-01T11:00:00-07:00" --location "Office" --contact <contact_id>
wbox events add "All-day event" --starts-at "2026-04-01T10:00:00-07:00" --ends-at "2026-04-01T11:00:00-07:00" --all-day --state confirmed
```

### Get

``` bash
wbox events get <event_id>
```

### Update

Pass only the fields you want to change:

``` bash
wbox events update <event_id> --title "Rescheduled Review"
wbox events update <event_id> --starts-at "2026-05-01T10:00:00-07:00" --ends-at "2026-05-01T11:00:00-07:00"
wbox events update <event_id> --state cancelled
wbox events update <event_id> --location "Conference Room B"
```

### Delete

``` bash
wbox events delete <event_id>
```

------------------------------------------------------------------------

## Notes

### List

``` bash
wbox notes list
wbox notes list --contact <id>
wbox notes list --project <id>
wbox notes list --opportunity <id>
wbox notes list --updated-since "2025-01-01T00:00:00Z"
wbox notes list --verbose   # show full content (default truncates to 500 chars)
```

### Add

``` bash
wbox notes add "Portfolio review call"
wbox notes add "Discussed estate plan" --contact <contact_id>
wbox notes add "Project kickoff notes" --contact <contact_id> --project <project_id>
```

### Get

``` bash
wbox notes get <note_id>
```

### Update

Pass only the fields you want to change:

``` bash
wbox notes update <note_id> --content "Updated note content"
wbox notes update <note_id> --contact <contact_id>
```

Note: Deleting notes is not supported via the Wealthbox v1 API.

------------------------------------------------------------------------

## Categories & Metadata

``` bash
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
```

The contact category types (contact-types, contact-sources, email-types, phone-types, address-types, website-types, contact-roles) are also reachable under `wbox contacts categories <name>`. `wbox events categories` and `wbox tasks categories` are aliases for `wbox categories event-categories` and `wbox categories task-categories`. Both forms call the same API endpoint.

### Custom Fields

``` bash
wbox categories custom-fields
wbox categories custom-fields --document-type Contact|Opportunity|Project|Task|Event|ManualInvestmentAccount|DataFile
```

------------------------------------------------------------------------

## Opportunities

### List

``` bash
wbox opportunities list
wbox opportunities list --resource-id <id> --resource-type Contact|Project
wbox opportunities list --order asc|desc|recent|created
wbox opportunities list --include-closed
wbox opportunities list --updated-since "2025-01-01T00:00:00Z"
wbox opportunities list --updated-before "2026-01-01T00:00:00Z"
wbox opportunities list --per-page 100 --page 2
```

### Add

Three fields are required: `--target-close`, `--probability`, and `--stage` (a stage ID — see `wbox categories opportunity-stages`):

``` bash
wbox opportunities add "New AUM Opportunity" \
  --target-close "2026-06-30" \
  --probability 75 \
  --stage <stage_id> \
  --contact <contact_id>
```

Amount fields:

``` bash
wbox opportunities add "Fee engagement" \
  --target-close "2026-09-30" \
  --probability 50 \
  --stage <stage_id> \
  --fee 5000.00 \
  --aum 250000.00 \
  --currency USD
```

Use `--more-fields` for uncommon fields not covered by direct flags (cannot override explicit flags):

``` bash
wbox opportunities add "Estate plan" \
  --target-close "2026-12-31" \
  --probability 60 \
  --stage <stage_id> \
  --more-fields '{"custom_fields": [{"id": 42, "value": "High priority"}]}'
```

### Get

``` bash
wbox opportunities get <opportunity_id>
```

### Update

Pass only the fields you want to change:

``` bash
wbox opportunities update <opportunity_id> --probability 90
wbox opportunities update <opportunity_id> --stage <stage_id>
wbox opportunities update <opportunity_id> --target-close "2026-12-31"
wbox opportunities update <opportunity_id> --aum 500000.00
wbox opportunities update <opportunity_id> --contact <contact_id>
```

### Delete

``` bash
wbox opportunities delete <opportunity_id>
```

------------------------------------------------------------------------

## Projects

### List

``` bash
wbox projects list
wbox projects list --updated-since "2025-01-01T00:00:00Z"
wbox projects list --updated-before "2026-01-01T00:00:00Z"
wbox projects list --per-page 100 --page 2
```

### Add

Both `name` and `--description` are required:

``` bash
wbox projects add "Client Onboarding" --description "New client onboarding workflow"
wbox projects add "Estate Review" --description "Annual estate plan review" --organizer <user_id>
```

Use `--more-fields` for uncommon fields not covered by direct flags:

``` bash
wbox projects add "Q4 Review" \
  --description "Quarterly review project" \
  --more-fields '{"custom_fields": [{"id": 5, "value": "urgent"}]}'
```

### Get

``` bash
wbox projects get <project_id>
```

### Update

Pass only the fields you want to change:

``` bash
wbox projects update <project_id> --name "Updated Project Name"
wbox projects update <project_id> --description "New description"
wbox projects update <project_id> --organizer <user_id>
```

------------------------------------------------------------------------

## Workflows

### List

``` bash
wbox workflows list
wbox workflows list --resource-id <id> --resource-type Contact|Project
wbox workflows list --status active|completed|scheduled
wbox workflows list --updated-since "2025-01-01T00:00:00Z"
wbox workflows list --per-page 100 --page 2
```

### Templates

List available workflow templates (needed for `wbox workflows add --template`):

``` bash
wbox workflows templates list
```

### Add

Create a new workflow instance from a template:

``` bash
wbox workflows add --template <template_id>
wbox workflows add --template <template_id> --label "Smith onboarding" --contact <contact_id>
wbox workflows add --template <template_id> --starts-at "2026-07-01" --project <project_id>
```

### Get

``` bash
wbox workflows get <workflow_id>
```

### Next Step

Show the active step (or completion status) of a workflow:

``` bash
wbox workflows next <workflow_id>
```

### Complete Step

Mark a workflow step as complete:

``` bash
wbox workflows complete-step <workflow_id> <step_id>
wbox workflows complete-step <workflow_id> <step_id> --outcome-id <outcome_id>
```

### Revert Step

Revert a completed workflow step:

``` bash
wbox workflows revert-step <workflow_id> <step_id>
```

------------------------------------------------------------------------

## Users

List all users in the workspace. Useful for resolving `--assigned-to` user IDs used by other commands:

``` bash
wbox users list
wbox users list --verbose
wbox users list --format table
```

------------------------------------------------------------------------

## Me

Show information about the currently authenticated user:

``` bash
wbox me
wbox me --format table
```

Print just the workspace user ID (a bare integer — useful for `--assigned-to` flags):

``` bash
wbox me user-id
```

------------------------------------------------------------------------

## Activity

The activity feed uses cursor-based pagination (not page/per-page).

### List

``` bash
wbox activity list
wbox activity list --contact <contact_id>
wbox activity list --type Task|Event|Contact|Workflow|Opportunity|Project
wbox activity list --updated-since "2025-01-01T00:00:00Z"
wbox activity list --updated-before "2026-01-01T00:00:00Z"
wbox activity list --verbose   # show full body content (default truncates to 500 chars)
```

Paginate with cursor:

``` bash
wbox activity list --cursor <cursor_from_previous_response>
```

------------------------------------------------------------------------

## Config

Manage the stored API token and CLI configuration. The token is stored in `~/.config/wbox/config.json` (Linux/macOS) or `%APPDATA%\wbox\config.json` (Windows).

### set-token

Prompt for and store an API token:

``` bash
wbox config set-token
wbox config set-token --token <your_token>
```

Obtain a token from Wealthbox at Settings → API Access → Access Tokens.

### show

Display current configuration (token is masked):

``` bash
wbox config show
```

### clear

Remove stored configuration:

``` bash
wbox config clear
```

------------------------------------------------------------------------

## Doctor

Comprehensive health check covering CLI version, auth, agent CLIs, skills, plugins, and firm data:

``` bash
wbox doctor
wbox doctor --token <override_token>
```

The `--token` flag overrides the env var and config file for the auth smoke test only.

------------------------------------------------------------------------

## Skills

Install and manage the `wealthbox-crm` agent skill across supported platforms (Claude Code user scope, Claude Code project scope, Codex).

### list

Show every skill copy installed on this machine:

``` bash
wbox skills list
```

### install

Install the skill to one or more platforms:

``` bash
wbox skills install --platform claude-code-user
wbox skills install --platform claude-code-project
wbox skills install --platform claude-code-user --platform codex
wbox skills install --platform claude-code-user --force   # overwrite existing install
wbox skills install --platform claude-code-user --no-bootstrap   # skip post-install bootstrap prompt
```

### upgrade

Refresh template files (`SKILL.md`, `references/`, `firm-examples/`, `bootstrap.md`) in every installed platform. Firm data is not touched:

``` bash
wbox skills upgrade
wbox skills upgrade --platform claude-code-user   # limit to one platform
```

### uninstall

Remove the skill from a platform. Firm data is preserved:

``` bash
wbox skills uninstall --platform claude-code-user
wbox skills uninstall --platform claude-code-user --yes   # skip confirmation
```

### bootstrap

Populate firm data from the Wealthbox API. Writes to the canonical machine-level firm directory:

``` bash
wbox skills bootstrap
wbox skills bootstrap --generated-only   # update generated files only; never create stubs
wbox skills bootstrap --dry-run          # print planned target; make no disk changes
```

### refresh

Re-fetch generated firm files. Hand-edited files are preserved:

``` bash
wbox skills refresh
wbox skills refresh --staleness-days 7   # warn if firm meta older than N days (default: 30)
```

### firm-path

Print the canonical firm data directory (useful from agents to locate `firm/` files):

``` bash
wbox skills firm-path
```

### mark-onboarded

Stamp `onboarded_at` in canonical firm meta after qualitative firm Q&A is captured:

``` bash
wbox skills mark-onboarded
```

### doctor

Alias of `wbox doctor` — diagnose install state, auth, and firm data:

``` bash
wbox skills doctor
```

------------------------------------------------------------------------

## Prefs

Read the user-preferences file (`~/.config/wbox/user/preferences.md`). The file is optional; commands exit `0` with empty output if it is absent.

### show

Print the contents of preferences.md:

``` bash
wbox prefs show
```

### path

Print the absolute path to preferences.md:

``` bash
wbox prefs path
```

------------------------------------------------------------------------

## Firm

Export, import, and diff the local firm archive. The firm directory holds hand-edited policy files used by the agent skill.

### export

Export the local firm directory as a portable zip archive. Only hand-edited policy files are included; generated files (`categories.md`, `custom-fields.md`, `users.md`) are excluded:

``` bash
wbox firm export
wbox firm export --out /path/to/firm.zip
```

### import

Import a firm-archive zip into the local firm directory. `PATH_OR_URL` may be a local file path or an HTTP(S) URL:

``` bash
wbox firm import firm.zip
wbox firm import https://example.com/firm.zip
wbox firm import firm.zip --mode merge            # write only new files; skip existing
wbox firm import firm.zip --mode abort-on-conflict  # refuse if any file would be replaced
wbox firm import firm.zip --yes                   # skip overwrite confirmation
```

### diff

Show a unified diff of a firm-archive zip against the local firm directory. Nothing is written to disk. Exits `0` when local matches the archive, non-zero when there are differences:

``` bash
wbox firm diff firm.zip
wbox firm diff firm.zip || echo "drift detected"
```

------------------------------------------------------------------------

## Self

Manage the `wbox` CLI binary itself.

### upgrade

Upgrade `wbox` to the latest GitHub release:

``` bash
wbox self upgrade
```

On Windows the replacement is deferred to the next launch (the running binary cannot replace itself). The outcome is reported on the following invocation.

------------------------------------------------------------------------

## Scripting Notes

### WBOX_BRIEF

Set `WBOX_BRIEF=1` (or pass `--brief` at the top level) to strip `*_html` fields from all output. Wealthbox duplicates every rich-text field as an HTML variant that is 3–5× larger; agents and pipelines almost never want it:

``` bash
# Linux/macOS
WBOX_BRIEF=1 wbox contacts get 123

# PowerShell
$env:WBOX_BRIEF="1"; wbox contacts list

# Inline flag (applies to all subcommands in the invocation)
wbox --brief contacts list --format table
```

### Internals (hidden)

`wbox internals` is a hidden sub-app for repo-maintenance tasks not intended for end users. It is accessible via `wbox internals --help` but is omitted from the top-level `wbox --help` listing. Currently it exposes `regen-skill-refs`, which regenerates flag tables in skill reference markdown files from the live Typer command tree.
