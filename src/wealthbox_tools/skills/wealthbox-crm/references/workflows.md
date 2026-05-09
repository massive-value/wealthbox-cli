# Workflows

Template-based process tracking. Created from templates, progressed by completing/reverting steps.

## List Workflows

```bash
wbox workflows list [OPTIONS]
```

| Flag | Type | Description |
|------|------|-------------|
| `--resource-id` | INT | Filter by linked resource ID |
| `--resource-type` | Contact\|Project | Type of linked resource |
| `--status` | active\|completed\|scheduled | Filter by status |
| `--updated-since` | ISO datetime | Modified after |
| `--updated-before` | ISO datetime | Modified before |
| `--page` | INT | Page number |
| `--per-page` | INT | Results per page |
| `--verbose`, `-v` | flag | Show all fields |
| `--format` | json\|table\|csv\|tsv | Output format |

## Get Workflow

```bash
wbox workflows <ID>
wbox workflows get <ID>
```

Supports `--no-comments`, `--verbose`, `--format`. Default output omits the
redundant `workflow_template` block (fetch separately via `templates list`);
pass `--verbose` to include it.

## Next Step

```bash
wbox workflows next <ID>
```

Returns the active step (or `{"completed": true, "completed_at": ...}` if the
workflow is done). Cheaper than parsing the full `get` response when you only
need to know "what's next."

## Create Workflow

```bash
wbox workflows add [OPTIONS]
```

| Flag | Type | Description |
|------|------|-------------|
| `--template` | INT | Workflow template ID (required) |
| `--label` | STR | Label/name for this instance |
| `--contact` | INT | Link to contact |
| `--project` | INT | Link to project |
| `--opportunity` | INT | Link to opportunity |
| `--visible-to` | STR | Visibility |
| `--starts-at` | STR | Start date |
| `--more-fields` | JSON | Additional fields |
| `--format` | json\|table\|csv\|tsv | Output format |

**Note:** Use `wbox workflows templates list` to find available template IDs.

## Complete Step

```bash
wbox workflows complete-step <WORKFLOW_ID> <STEP_ID> [OPTIONS]
```

| Flag | Type | Description |
|------|------|-------------|
| `--outcome-id` | INT | Outcome selection |
| `--due-date` | STR | For restarting a step |
| `--due-date-set` | flag | Whether restarted step has due date |
| `--no-advance-hint` | flag | Skip the post-complete workflow fetch + stderr summary |
| `--format` | json\|table\|csv\|tsv | Output format |

After a successful complete-step, the CLI fetches the workflow and prints a
one-line summary to **stderr** describing the new active step (or that the
workflow completed). Stdout stays the raw API response. Wealthbox's complete-step
response itself does not say which outcome was selected, so this hint is the
fastest way to confirm branching took effect.

## Revert Step

```bash
wbox workflows revert-step <WORKFLOW_ID> <STEP_ID> [OPTIONS]
```

## List Templates

```bash
wbox workflows templates list [OPTIONS]
```

Same filter flags as workflow list.

## Generated Flag Reference

The following section is auto-generated from the Typer command tree by
`wbox internals regen-skill-refs`. Do not hand-edit between the markers —
edits will be overwritten on the next regen pass.

<!-- auto-gen:flags -->
### `wbox workflows add`

Create a new workflow from a template.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--contact` | `INTEGER` | `-` | Link to a Contact by ID |
| `--format` | `CHOICE` | `json` |  |
| `--label` | `TEXT` | `-` | Optional label for this workflow instance |
| `--more-fields` | `TEXT` | `-` | JSON object for additional fields (e.g. workflow_milestones) |
| `--opportunity` | `INTEGER` | `-` | Link to an Opportunity by ID |
| `--project` | `INTEGER` | `-` | Link to a Project by ID |
| `--starts-at` | `TEXT` | `-` | Start date (e.g. 2026-06-01) |
| `--template` | `INTEGER` | `-` | Workflow template ID — see: wbox workflows templates list |
| `--visible-to` | `TEXT` | `-` |  |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

### `wbox workflows complete-step`

Mark a workflow step as complete.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--due-date` | `TEXT` | `-` | Due date when restarting a step (requires --due-date-set) |
| `--due-date-set` | `BOOLEAN` | `false` | Whether the restarted step has a due date |
| `--format` | `CHOICE` | `json` |  |
| `--no-advance-hint` | `BOOLEAN` | `false` | Skip the follow-up GET that summarizes the new active step (saves one API call). |
| `--outcome-id` | `INTEGER` | `-` | Workflow outcome ID (if step has multiple outcomes) |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

### `wbox workflows get`

Get a single workflow by ID.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--format` | `CHOICE` | `json` |  |
| `--no-comments` | `BOOLEAN` | `false` | Omit comments from output |
| `--verbose` / `-v` | `BOOLEAN` | `false` | Show all fields including the full template |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

### `wbox workflows list`

List workflows with optional filters.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--format` | `CHOICE` | `json` |  |
| `--page` | `INTEGER` | `-` |  |
| `--per-page` | `INTEGER` | `-` | Results per page (max 100) |
| `--resource-id` | `INTEGER` | `-` | Filter by linked resource ID (requires --resource-type) |
| `--resource-type` | `CHOICE` | `-` | Filter by linked resource type: Contact, Project |
| `--status` | `CHOICE` | `-` | active, completed, or scheduled |
| `--updated-before` | `TEXT` | `-` |  |
| `--updated-since` | `TEXT` | `-` |  |
| `--verbose` / `-v` | `BOOLEAN` | `false` | Show all fields |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

**Choices for `--resource-type`:**

- `Contact`
- `Project`

**Choices for `--status`:**

- `active`
- `completed`
- `scheduled`

### `wbox workflows next`

Show the active step (or completion status) of a workflow.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--format` | `CHOICE` | `json` |  |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

### `wbox workflows revert-step`

Revert a completed workflow step.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--format` | `CHOICE` | `json` |  |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

### `wbox workflows templates list`

List available workflow templates.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--format` | `CHOICE` | `json` |  |
| `--page` | `INTEGER` | `-` |  |
| `--per-page` | `INTEGER` | `-` | Results per page (max 100) |
| `--resource-id` | `INTEGER` | `-` | Filter by linked resource ID |
| `--resource-type` | `CHOICE` | `-` | Filter by linked resource type: Contact, Project |
| `--status` | `CHOICE` | `-` | active, completed, or scheduled |
| `--updated-before` | `TEXT` | `-` |  |
| `--updated-since` | `TEXT` | `-` |  |
| `--verbose` / `-v` | `BOOLEAN` | `false` | Show all fields |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`

**Choices for `--resource-type`:**

- `Contact`
- `Project`

**Choices for `--status`:**

- `active`
- `completed`
- `scheduled`
<!-- /auto-gen:flags -->

## Examples

```bash
# List available templates
wbox workflows templates list --format table

# Start onboarding workflow for a contact
wbox workflows add --template 123 --contact 67890 --label "Smith Onboarding"

# Complete a workflow step
wbox workflows complete-step 111 222

# Just tell me what's next
wbox workflows next 111
```

## Quirks (verified against the live API)

- **`completed_at` — not `active_step` — is the truth signal.** When a workflow
  completes, Wealthbox does not clear the `active_step` field — it keeps
  pointing at the final completed step. To detect completion, check that
  `completed_at` is non-empty. `wbox workflows next` already handles this.
- **`due_date` is materialized at step *activation*, not workflow creation.**
  Steps further down the chain return `due_date: ""` until they become the
  active step. Empty string ≠ "no due date scheduled" — it just means "not yet
  reached."
- **Empty strings, not nulls, for unset datetimes.** `completed_at: ""`,
  `due_date: ""`. If you ever add a Pydantic output model with
  `datetime | None`, you must coerce empty strings to None.
- **`complete-step` response doesn't surface the selected outcome.** It returns
  the step with *all* of its possible outcomes attached, identical shape to the
  pre-completion read. To verify branching worked, re-fetch the workflow and
  inspect the new `active_step` (or just rely on the CLI's stderr advance hint).
- **Skipped steps stay `pending`.** When an outcome jumps over intermediate
  steps, those steps are NOT marked skipped or completed — they have empty
  `completed_at` and `due_date`, indistinguishable from steps that simply
  haven't been reached. Outcome-driven workflows can revisit earlier steps, so
  "later step is completed" doesn't reliably imply "earlier step was skipped."
- **`revert-step` preserves `due_date`.** Reverting only clears `completed_at`
  and `completer_id`; the previously materialized `due_date` is kept.
- **Workflows attach to either the household or any member.** When looking up a
  client's workflows, check both the household contact and each member contact —
  Wealthbox does not roll member workflows up to the household.
- **Instance `name` is lower-cased relative to template `name`.** Template
  "Auto Trade Enrollment" becomes instance "Auto trade enrollment". Cosmetic.
- **`workflow_template` is included on every workflow list/get response.** It's
  the full template (every step + html descriptions). The CLI strips it from
  default output to save tokens; pass `--verbose` to include it.
