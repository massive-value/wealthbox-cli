---
name: wealthbox-crm
description: Use when the user wants to interact with Wealthbox CRM — creating, updating, listing, or looking up contacts, tasks, notes, events, opportunities, projects, workflows, households, categories, users, or activity. Also use when the user describes CRM workflows like onboarding clients, logging meetings, or assigning follow-ups.
---

# Wealthbox CRM

Execute Wealthbox CRM operations via the `wbox` CLI. Supports contacts, tasks, notes, events,
opportunities, projects, workflows, households, and read-only lookups (categories, users, activity, me).

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
3. **Check firm config** — if `firm-config.md` exists in this skill's directory, read it and apply the relevant section's requirements (required fields, defaults, naming conventions)
4. **Fill gaps** — if required information is missing, ask the user. Prefer multiple-choice when options are known (e.g., contact type, priority level). If the user is unfamiliar with Wealthbox, explain what the field means.
5. **Execute** — run the `wbox` command(s) via Bash
6. **Report** — show the result. For create/update, confirm what was created with the record ID.

## Multi-Step Workflows

When firm-config.md defines named workflows (e.g., "onboarding", "meeting followup"):
1. Read the workflow definition from firm-config.md
2. Load all referenced resource reference files
3. Walk through each step, gathering input as needed
4. Execute commands in sequence, passing IDs forward (e.g., new contact ID → linked note/task)

## Output Format

- Default to `--format json` for single records, `--format table` for lists
- If the user asks to "show" or "display", use `--format table`
- If the user is piping or scripting, use `--format json`

## Patterns to Know

- **ID shorthand:** `wbox contacts 123` is the same as `wbox contacts get 123`
- **Linking:** most resources accept `--contact ID`, `--project ID`, `--opportunity ID`
- **More fields:** `--more-fields '{"key": "value"}'` for fields without dedicated flags
- **Dates:** use `YYYY-MM-DD` for dates, `YYYY-MM-DDTHH:MM:SS-07:00` for datetimes
- **Activity pagination:** uses `--cursor`, not `--page`
