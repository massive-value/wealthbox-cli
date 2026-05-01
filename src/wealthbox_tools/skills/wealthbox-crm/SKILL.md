---
name: wealthbox-crm
description: Use when the user wants to interact with Wealthbox CRM — creating, updating, listing, or looking up contacts, tasks, notes, events, opportunities, projects, workflows, households, categories, users, or activity. Also use when the user describes CRM workflows like onboarding clients, logging meetings, or assigning follow-ups.
---

# Wealthbox CRM

Execute Wealthbox CRM operations via the `wbox` CLI. Supports contacts, tasks, notes, events,
opportunities, projects, workflows, households, and read-only lookups (categories, users, activity, me).

## First Run

If `_meta.json` in this skill's directory does **not** contain a `firm`
section, the firm has not been onboarded yet on this machine. Before
handling the user's request:

1. Read `bootstrap.md` in this skill's directory.
2. Follow it end-to-end.
3. The bootstrap will populate `_meta.json.firm` so this check passes
   on subsequent runs.

## Staleness Check

`_meta.json.template.cli_version` records which `wbox` version installed
the template files. Compare it to the running CLI version:

```bash
wbox --version
```

If the template version is older, suggest the user run:

```bash
wbox skills upgrade
```

This refreshes SKILL.md, references/, firm-examples/, and bootstrap.md
across every installed platform while preserving `firm/`.

## Prerequisites

- `wbox` CLI installed (`pip install wealthbox-cli`)
- Token configured via one of: `wbox config set-token`, `WEALTHBOX_TOKEN` env var, or `.env` file

Verify with: `wbox me`

## Command Map

| Intent | Resource | Command Pattern |
|--------|----------|-----------------|
| Find/list contacts | contacts | `wbox contacts list [filters]` |
| Get a contact | contacts | `wbox contacts get <ID>` or `wbox contacts <ID>` |
| Create a contact | contacts | `wbox contacts add {person\|household\|org\|trust} [flags]` |
| Update a contact | contacts | `wbox contacts update <ID> [flags]` |
| Delete a contact | contacts | `wbox contacts delete <ID>` |
| List/get/add/update tasks | tasks | `wbox tasks {list\|get\|add\|update\|delete} ...` |
| List/get/add/update notes | notes | `wbox notes {list\|get\|add\|update} ...` |
| List/get/add/update events | events | `wbox events {list\|get\|add\|update\|delete} ...` |
| Opportunities | opportunities | `wbox opportunities {list\|get\|add\|update\|delete} ...` |
| Projects | projects | `wbox projects {list\|get\|add\|update} ...` |
| Workflows | workflows | `wbox workflows {list\|get\|add\|complete-step\|revert-step} ...` |
| Household members | households | `wbox households {add-member\|remove-member} ...` |
| Categories/tags | lookups | `wbox categories ...` or `wbox <resource> categories` |
| Users | lookups | `wbox users list` |
| Activity feed | lookups | `wbox activity list [filters]` |
| Current user | lookups | `wbox me` |

## Workflow

1. **Parse intent** — identify which resource(s) and action(s) the user needs
2. **Load reference** — read ONLY the relevant `references/<resource>.md` file(s) from this skill's directory
3. **Check firm config** — read `firm/<resource>.md` for the resource(s) you're touching. Also read `firm/categories.md` and `firm/custom-fields.md` when you need valid values for category-constrained flags (avoid repeat API probes).
4. **Fill gaps** — if required information is missing, ask the user. Prefer multiple-choice when options are known (e.g., contact type, priority level). If the user is unfamiliar with Wealthbox, explain what the field means.
5. **Execute** — run the `wbox` command(s) via Bash
6. **Report** — show the result. For create/update, confirm what was created with the record ID.

## Multi-Step Workflows

When `firm/workflows.md` defines named workflows (e.g., "onboarding", "meeting followup"):
1. Read the workflow definition from `firm/workflows.md`
2. Load all referenced resource reference files
3. Walk through each step, gathering input as needed
4. Execute commands in sequence, passing IDs forward (e.g., new contact ID → linked note/task)

## Output Format

- Default to `--format json` for single records, `--format table` for lists
- If the user asks to "show" or "display", use `--format table`
- If the user is piping or scripting, use `--format json`

## Common Recipes

**Find then act.** Almost every operation starts by resolving a name to an ID:

```bash
wbox contacts list --name "Smith" --type Household --format json
# read the id from output, then:
wbox notes add "Discussed Roth conversion." --contact <ID>
```

Use `--name` for contains-match name search (not `--search`). Combine with `--type` and `--contact-type` to narrow.

**Multi-line content with shell-special characters.** The note/task body is a positional arg, so `$`, backticks, and `!` will be interpolated by bash. Three safe patterns:

```bash
# 1. Single quotes — no interpolation, simplest for one-liners
wbox notes add 'Q1 distribution of $5,000 sent on 4/27.' --contact 123

# 2. Heredoc via command substitution — best for multi-paragraph
wbox notes add "$(cat <<'EOF'
Subject: SS Analysis follow-up

Sent the MaxiFi report on 4/27. Awaiting reply.
Strategy: defer to age 70, ~$48,000/yr.
EOF
)" --contact 123

# 3. Read from a file
wbox notes add "$(cat /tmp/note.md)" --contact 123
```

The single-quoted heredoc (`<<'EOF'`) is the recommended default — it disables all bash expansion inside the body.

## Patterns to Know

- **ID shorthand:** `wbox contacts 123` is the same as `wbox contacts get 123`
- **Linking:** most resources accept `--contact ID`, `--project ID`, `--opportunity ID`
- **More fields:** `--more-fields '{"key": "value"}'` for fields without dedicated flags
- **Dates:** use `YYYY-MM-DD` for dates, `YYYY-MM-DDTHH:MM:SS-07:00` for datetimes
- **Relative due dates:** tasks accept `--frame today|tomorrow|this-week|next-week|this-month|next-month` instead of `--due-date` (mutually exclusive)
- **Activity pagination:** uses `--cursor`, not `--page`
- **Don't infer flag names:** read `references/<resource>.md` before invoking — flags like `--name` (not `--search`), `--frame` (not `--due-in`) are easy to guess wrong
