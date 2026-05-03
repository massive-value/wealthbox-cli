# First-Run Bootstrap

You were told to read this because `<firm>/_meta.json.onboarded_at` is missing
on this machine — where `<firm>` is the canonical firm directory printed by
`wbox skills firm-path`. Follow every step below, then run the marker command
in Step 4 so this bootstrap path is skipped on future invocations.

## Step 1 — Fetch API-derived firm data

First, find the firm directory:

```bash
wbox skills firm-path
```

Cache that path. If `<firm>/_meta.json` already exists with an `identity` and
`files` map, the CLI bootstrap has already run on this machine and you can
skip to Step 2. Otherwise, run:

```bash
wbox skills bootstrap
```

It populates these files at the canonical firm path (machine-level — survives
plugin auto-updates and skill template upgrades):

- `<firm>/categories.md` — every category type + valid values (paginated; complete)
- `<firm>/custom-fields.md` — custom fields per document type + valid values (paginated; complete)
- `<firm>/users.md` — user id -> name -> email (paginated; complete)
- `<firm>/_meta.json` — firm identity, refresh timestamps, and the CLI version
  that ran the bootstrap. Does **not** set `onboarded_at` — that's Step 4.
- Stub files: `<firm>/contacts.md`, `<firm>/tasks.md`, `<firm>/notes.md`,
  `<firm>/events.md`, `<firm>/opportunities.md`, `<firm>/projects.md`,
  `<firm>/workflows.md` — one-line TODOs you will fill in next.

Verify `<firm>/_meta.json` now exists with an `identity` key before continuing.

## Step 2 — Gather firm policy (per-resource)

For each hand-edited stub below, open `firm-examples/<resource>.md` (alongside
this `bootstrap.md` in the skill directory) to see a filled-in example, then
ask the advisor the listed questions. Record answers in
`<firm>/<resource>.md`, replacing the stub TODO.

Read `<firm>/categories.md` and `<firm>/custom-fields.md` first so every
multiple-choice prompt offers **real** values from the firm's workspace.
If the advisor mentions a tag, custom-field option, or user that you can't
find in those files, flag it — they're generated from a paginated fetch and
*should* be complete. A missing entry usually means the value doesn't exist
in the workspace yet (rather than a pagination gap).

### `<firm>/contacts.md`

- Default contact type for new people? (pick from `<firm>/categories.md` ->
  contact_types)
- Default contact source? (contact_sources)
- Default assigned-to user? (pick from `<firm>/users.md`)
- Preferred email type? (email_types)
- Preferred phone type? (phone_types)
- Household naming convention? (e.g. `"The {LastName} Family"`)
- When should a household be created automatically? (e.g. married couple)
- Required fields for person / household / org / trust?

### `<firm>/tasks.md`

- Default priority when unspecified?
- Default assigned-to rule? (e.g. same as linked contact)
- Default due-date frame? (today / this-week / next-week / this-month)
- Named task templates the firm reuses? (e.g. "Welcome call", "Collect
  documents") — include name, priority, frame, description for each.

### `<firm>/notes.md`

- Prefix or format convention for meeting notes?
- Are notes always linked to a contact (never orphan)?

### `<firm>/events.md`

- Default state? (confirmed, tentative)
- Default meeting duration?
- Event naming convention?

### `<firm>/opportunities.md`

- Default pipeline? (from opportunity_pipelines)
- Default stage for new prospects? (from opportunity_stages)
- Default probability?
- Required fields on create?

### `<firm>/projects.md`

- Any standard project templates?
- Conventions for linking projects to contacts?

### `<firm>/workflows.md`

- Workflow templates the firm uses, with template IDs.
- Named multi-step workflows. Common ones:
  - **Onboarding**: contact -> household -> intake note -> tasks -> opportunity -> workflow
  - **Meeting followup**: note -> action-item tasks -> (optional) opportunity update
  - **Annual review**: event -> workflow -> note

## Step 3 — Catch-all

Ask the advisor: "Is there any firm convention, custom process, or preference
I haven't asked about that I should follow?" Append freeform answers to
`<firm>/workflows.md` under a `## Other Conventions` heading.

## Step 4 — Mark the firm onboarded

Run:

```bash
wbox skills mark-onboarded
```

This stamps `onboarded_at` in `<firm>/_meta.json`. The First Run check in
`SKILL.md` keys off this field, so future invocations will skip the
bootstrap path automatically.

## Step 5 — Confirm and continue

Tell the advisor: "First-run setup complete — firm data populated for <firm
name>." Then return to the user's original request.

You don't need to delete this file or trim `SKILL.md`. The first-run check
keys on `<firm>/_meta.json.onboarded_at`, which now exists.
