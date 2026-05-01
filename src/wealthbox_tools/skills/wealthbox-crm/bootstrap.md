# First-Run Bootstrap

You were told to read this because `_meta.json` in the skill root does not
contain a `firm` section. Follow every step below.

## Step 1 — Fetch API-derived firm data

Run this command:

```bash
wbox skills bootstrap
```

It populates these files per installed platform:

- `firm/categories.md` — every category type + valid values
- `firm/custom-fields.md` — custom fields per document type + valid values
- `firm/users.md` — user id → name → email
- `_meta.json` (skill root) — adds the `firm` section: identity, refresh
  timestamps, and the CLI version that ran the bootstrap
- Stub files: `firm/contacts.md`, `firm/tasks.md`, `firm/notes.md`,
  `firm/events.md`, `firm/opportunities.md`, `firm/projects.md`,
  `firm/workflows.md` — one-line TODOs you will fill in next.

Verify the `firm` section now exists in `_meta.json` before continuing.

## Step 2 — Gather firm policy (per-resource)

For each hand-edited stub below, open `firm-examples/<resource>.md` to see a
filled-in example, then ask the advisor the listed questions. Record answers
in `firm/<resource>.md`, replacing the stub TODO.

Read `firm/categories.md` and `firm/custom-fields.md` first so every
multiple-choice prompt offers **real** values from the firm's workspace.

### firm/contacts.md

- Default contact type for new people? (pick from `firm/categories.md` →
  contact_types)
- Default contact source? (contact_sources)
- Default assigned-to user? (pick from `firm/users.md`)
- Preferred email type? (email_types)
- Preferred phone type? (phone_types)
- Household naming convention? (e.g. `"The {LastName} Family"`)
- When should a household be created automatically? (e.g. married couple)
- Required fields for person / household / org / trust?

### firm/tasks.md

- Default priority when unspecified?
- Default assigned-to rule? (e.g. same as linked contact)
- Default due-date frame? (today / this-week / next-week / this-month)
- Named task templates the firm reuses? (e.g. "Welcome call", "Collect
  documents") — include name, priority, frame, description for each.

### firm/notes.md

- Prefix or format convention for meeting notes?
- Are notes always linked to a contact (never orphan)?

### firm/events.md

- Default state? (confirmed, tentative)
- Default meeting duration?
- Event naming convention?

### firm/opportunities.md

- Default pipeline? (from opportunity_pipelines)
- Default stage for new prospects? (from opportunity_stages)
- Default probability?
- Required fields on create?

### firm/projects.md

- Any standard project templates?
- Conventions for linking projects to contacts?

### firm/workflows.md

- Workflow templates the firm uses, with template IDs.
- Named multi-step workflows. Common ones:
  - **Onboarding**: contact → household → intake note → tasks → opportunity → workflow
  - **Meeting followup**: note → action-item tasks → (optional) opportunity update
  - **Annual review**: event → workflow → note

## Step 3 — Catch-all

Ask the advisor: "Is there any firm convention, custom process, or preference
I haven't asked about that I should follow?" Append freeform answers to
`firm/workflows.md` under a `## Other Conventions` heading.

## Step 4 — Confirm and continue

Tell the advisor: "First-run setup complete — `firm/` populated for <firm
name>." Then return to the user's original request.

You don't need to delete this file or trim `SKILL.md`. The first-run check
keys on `_meta.json.firm`, which now exists, so the bootstrap path will be
skipped on every subsequent invocation automatically.
