# Comments

Comments are the conversation thread on a work record. In the Wealthbox UI they
carry most of the back-and-forth on tasks and workflow steps, so they are often
where the actual context lives.

## Read-only here, writable elsewhere

`wbox` has no `comments add`, because the REST API it speaks cannot write one.
`POST /v1/comments` returns a response byte-identical to a nonexistent path, as
does `POST /v1/tasks/{id}/comments`. The v1 API exposes `GET /comments` only.

Comment writes do exist, on a different surface. `POST /comments` without the
`/v1` prefix (and the same path on `app.crmworkspace.com`) returns 302 to
`/users/login`: it is a session-authenticated web route, not a token one. The
official Wealthbox MCP server at `mcp.crmworkspace.com` reaches it over OAuth
and exposes a `CreateComment` tool. Two tells that it is a different API: it
requires an `account_id`, which the v1 API has no concept of, and it accepts
`Contact` as a `resource_type`, which `GET /v1/comments` rejects.

So if you have the Wealthbox MCP available, write comments with its
`CreateComment` and read them with `wbox` — a comment created through the MCP
shows up immediately in `wbox comments list` and inline in `wbox tasks get`.
With only an API token, the durable alternatives are a note (`wbox notes add`)
or the record's description.

## Two ways to read them

Comments already come back inline on `get`:

```bash
wbox tasks get 12345            # comments included by default
wbox tasks get 12345 --no-comments
```

That works for tasks, events, notes, opportunities, projects, and workflows.
Contacts are the exception: `/comments` rejects `Contact` as a `resource_type`,
so `wbox contacts get` has no comment flag.

Use `wbox comments list` when you want comments on their own, across a window
rather than one record at a time.

## List Comments

```bash
wbox comments list [OPTIONS]
```

| Flag | Type | Description |
|------|------|-------------|
| `--task` | INT | Comments on a task |
| `--event` | INT | Comments on an event |
| `--note` | INT | Comments on a note (`StatusUpdates` on the wire) |
| `--opportunity` | INT | Comments on an opportunity |
| `--project` | INT | Comments on a project |
| `--workflow` | INT | Comments on a workflow |
| `--updated-since` | ISO datetime | Modified after |
| `--updated-before` | ISO datetime | Modified before |
| `--page` | INT | Page number |
| `--per-page` | INT | Results per page (max 100) |
| `--verbose`, `-v` | flag | Show all fields, including the html body |
| `--format` | json\|table\|csv\|tsv | Output format |

Pass at most one resource flag.

## Always filter

An unfiltered `GET /comments` scans every comment in the workspace at roughly
8.5 seconds per page of 100. A one-month `--updated-since`/`--updated-before`
window brings that to about 1.5 seconds per page. `wbox comments list` refuses
a call with neither a resource nor a window and exits 1 rather than let an agent
find that out by waiting.

## Resource types you may see

`resource_type` values observed on the wire: `Task`, `StatusUpdate` (a note),
`Event`, `Opportunity`, `Workflow`, `WorkflowStep`, `SelectedOutcome`.

`SelectedOutcome` IDs appear nowhere else in the API, so a comment attached to
one cannot be joined back to the workflow step that produced it. If you need to
reconstruct a workflow's discussion, read the `Workflow` and `WorkflowStep`
comments and treat `SelectedOutcome` ones as orphans.

## Generated Flag Reference

The following section is auto-generated from the Typer command tree by
`wbox internals regen-skill-refs`. Do not hand-edit between the markers —
edits will be overwritten on the next regen pass.

<!-- auto-gen:flags -->
### `wbox comments list`

List comments for one record, or for a time window. Requires a resource filter or --updated-since/--updated-before.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--event` | `INTEGER` | `-` | Comments on an Event (by ID) |
| `--format` | `CHOICE` | `json` |  |
| `--note` | `INTEGER` | `-` | Comments on a Note (by ID) |
| `--opportunity` | `INTEGER` | `-` | Comments on an Opportunity (by ID) |
| `--page` | `INTEGER` | `-` | Page number |
| `--per-page` | `INTEGER` | `-` | Results per page (max 100) |
| `--project` | `INTEGER` | `-` | Comments on a Project (by ID) |
| `--task` | `INTEGER` | `-` | Comments on a Task (by ID) |
| `--updated-before` | `TEXT` | `-` | ISO 8601 datetime |
| `--updated-since` | `TEXT` | `-` | ISO 8601 datetime |
| `--verbose` / `-v` | `BOOLEAN` | `false` | Show all fields |
| `--workflow` | `INTEGER` | `-` | Comments on a Workflow (by ID) |

**Choices for `--format`:**

- `csv`
- `json`
- `table`
- `tsv`
<!-- /auto-gen:flags -->

## Examples

```bash
# The thread on one task
wbox comments list --task 12345 --format table

# Everything commented on in the last month
wbox comments list --updated-since 2026-08-20T00:00:00-06:00 --format table

# A workflow's discussion
wbox comments list --workflow 3522997
```
