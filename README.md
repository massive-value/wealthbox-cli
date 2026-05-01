# Wealthbox CLI — Command-Line Client for the Wealthbox CRM API

[![PyPI version](https://img.shields.io/pypi/v/wealthbox-cli)](https://pypi.org/project/wealthbox-cli/)
[![Downloads](https://img.shields.io/pypi/dm/wealthbox-cli)](https://pypi.org/project/wealthbox-cli/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/downloads/)
[![CI](https://img.shields.io/github/actions/workflow/status/massive-value/wealthbox-cli/ci.yml?label=CI)](https://github.com/massive-value/wealthbox-cli/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

**wealthbox-cli** (`wbox`) is a command-line tool and Python client library for the [Wealthbox CRM](https://www.wealthbox.com/) API. It gives financial advisors, developers, and RIA firms full CRUD access to contacts, tasks, events, notes, households, and more — directly from the terminal. Automate your CRM workflows, export data, and integrate Wealthbox into scripts and CI pipelines.

[Documentation](https://massive-value.github.io/wealthbox-cli/) | [PyPI](https://pypi.org/project/wealthbox-cli/) | [Changelog](https://massive-value.github.io/wealthbox-cli/changelog/) | [Wealthbox CRM](https://www.wealthbox.com/) | [Wealthbox API Docs](https://dev.wealthbox.com)

> **Disclaimer:** This is an unofficial, community-built tool. It is not affiliated with,
> endorsed by, or supported by Wealthbox or its parent company. "Wealthbox" is a trademark
> of its respective owner.

------------------------------------------------------------------------

## Why Use wealthbox-cli?

- **No coding required** — structured CLI flags replace raw JSON and cURL commands
- **Automate CRM workflows** — script bulk updates, data exports, and scheduled tasks
- **Multiple output formats** — pipe JSON, CSV, or TSV directly to files or other tools
- **Built for financial advisors and developers** — covers contacts, households, tasks, events, notes, categories, and custom fields
- **AI-agent ready** — pair with [Claude Code](https://claude.ai/download) or other coding agents for natural-language CRM automation
- **Open source** — Apache 2.0 licensed, community-driven, and extensible

------------------------------------------------------------------------

## Quick Start

```bash
pip install wealthbox-cli
wbox config set-token        # paste your Wealthbox API token (masked)
wbox me                      # verify connection
```

See the [Getting Started](https://massive-value.github.io/wealthbox-cli/getting-started/) guide for pipx install, environment variable auth, and other options.

------------------------------------------------------------------------

## Usage Examples

```bash
# List contacts as a table
wbox contacts list --format table

# Create a new client contact
wbox contacts add person --first-name Jane --last-name Doe --contact-type Client

# Export tasks to CSV
wbox tasks list --format csv > tasks.csv

# Create a task linked to a contact
wbox tasks add "Follow up call" --due-date "2026-04-10T09:00:00-07:00" --contact 12345

# Add a meeting note
wbox notes add "Discussed retirement plan" --contact 12345

# Schedule an event
wbox events add "Annual Review" --starts-at "2026-05-01T10:00:00-07:00" --ends-at "2026-05-01T11:00:00-07:00"
```

For the full command list, see the [CLI Reference](https://massive-value.github.io/wealthbox-cli/cli-reference/).

------------------------------------------------------------------------

## Supported Resources

| Resource | List | Get | Create | Update | Delete |
|----------|:----:|:---:|:------:|:------:|:------:|
| Contacts | Yes | Yes | Yes | Yes | Yes |
| Households | Yes | Yes | Yes | Yes | Yes |
| Tasks | Yes | Yes | Yes | Yes | Yes |
| Events | Yes | Yes | Yes | Yes | Yes |
| Notes | Yes | Yes | Yes | Yes | — |
| Users | Yes | — | — | — | — |
| Activity | Yes | — | — | — | — |
| Categories | Yes | — | — | — | — |

------------------------------------------------------------------------

## Use with AI Coding Agents

wealthbox-cli ships with a skill for [Claude Code](https://claude.ai/download) and [Codex](https://openai.com/codex) that lets AI agents manage your CRM through natural language. Instead of memorizing CLI flags, just describe what you want:

```
create a contact for Jane Doe, she's a new prospect
list my tasks due this week
add a note to contact 123 about today's meeting
find all contacts tagged "VIP" and export to CSV
```

The skill translates your intent into the correct `wbox` commands, handles flag construction, and validates inputs — ideal for advisors who want CRM automation without learning CLI syntax.

### Install

One command, same on every OS:

```bash
pip install wealthbox-cli
wbox config set-token        # paste your Wealthbox API token
wbox skills install          # interactive: pick Claude Code, Codex, or both
```

The installer asks which platforms to target, copies the skill into the right directory (`~/.claude/skills/` for Claude Code, `~/.codex/skills/` for Codex — with `SKILL.md` renamed to `AGENTS.md` automatically), and offers to bootstrap your firm's customizations from the Wealthbox API.

### First agent run bootstraps itself

The first time an agent invokes the skill, it walks you through populating firm-specific conventions — category values, custom fields, users, defaults, required fields, household naming, named workflows. No further CLI commands needed. After that first run, the bootstrap artifacts self-delete from the skill.

### Refresh after firm changes

If your firm adds or renames category values, custom fields, or users:

```bash
wbox skills refresh
```

This updates the generated half of the skill's firm files; hand-edited policy is preserved.

### Other commands

```bash
wbox skills list             # show where the skill is installed + last bootstrap time
wbox skills doctor           # diagnose install state + token
wbox skills sync             # copy firm/ from one install to others (Claude Code <-> Codex)
wbox skills uninstall        # remove the skill
```

`wbox skills sync` is useful if you maintain firm conventions in one platform's install (e.g., your Claude Code user scope) and want the same `firm/` files mirrored to Codex or to a project-scoped `.claude/skills/` folder. The command runs as a wizard by default; pass `--source`, `--target`, and `--yes` for non-interactive use.

### Works with other agents too

The `wbox` CLI is a standard command-line tool. Any AI coding agent that can execute shell commands — [Claude Code](https://claude.ai/download), [GitHub Copilot CLI](https://githubnext.com/projects/copilot-cli), [Cursor](https://cursor.sh/), or custom agent frameworks — can use it to read and write Wealthbox data. The bundled skill just makes Claude Code and Codex aware of the full command surface.

------------------------------------------------------------------------

## Architecture

```
src/wealthbox_tools/
    cli/        # Typer commands — user-facing, delegates to client
    client/     # Async HTTP client built from mixins
    models/     # Pydantic v2 models for input validation
```

Built with [Typer](https://typer.tiangolo.com/), [httpx](https://www.python-httpx.org/), and [Pydantic v2](https://docs.pydantic.dev/). See [Contributing](https://massive-value.github.io/wealthbox-cli/contributing/) for the full architecture guide and how to add new resources.

------------------------------------------------------------------------

## Contributing

```bash
git clone https://github.com/massive-value/wealthbox-cli
cd wealthbox-cli
python -m venv .venv
```

Activate the virtual environment:

| Platform | Command |
|----------|---------|
| macOS/Linux | `source .venv/bin/activate` |
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` |
| Windows (Command Prompt) | `.venv\Scripts\activate.bat` |

Then install and test:

```bash
pip install -e ".[dev]"
pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

------------------------------------------------------------------------

## Troubleshooting

**401 Unauthorized** — Check your API token. Run `wbox config show` to verify.

**Date format errors** — Use ISO 8601: `"2026-04-01T10:00:00-07:00"` or `"2026-04-01T10:00:00Z"`. Date-only fields use `"YYYY-MM-DD"`.

**Writes appear to succeed but nothing changed** — Some category-constrained writes silently no-op. Check valid values first with `wbox contacts categories contact-types`.

------------------------------------------------------------------------

## Disclaimer

This is an **unofficial, community-built** tool. It is not affiliated with, endorsed by,
or supported by Wealthbox or its parent company. "Wealthbox" is a trademark of its
respective owner. Use of this tool is subject to the [Wealthbox API Terms of Service](https://dev.wealthbox.com).

------------------------------------------------------------------------

## License

Apache 2.0 — see [LICENSE](LICENSE).
