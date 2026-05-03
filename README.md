# Wealthbox CLI

**Run your Wealthbox CRM through Claude or ChatGPT.** Tell your AI agent *"add a contact for Jane Doe, send her our welcome packet, and put a follow-up on my calendar for next Tuesday"* — and it just happens. No coding, no Python, no terminal commands to memorize.

[![PyPI](https://img.shields.io/pypi/v/wealthbox-cli)](https://pypi.org/project/wealthbox-cli/) [![Downloads](https://img.shields.io/pypi/dm/wealthbox-cli)](https://pypi.org/project/wealthbox-cli/) [![CI](https://img.shields.io/github/actions/workflow/status/massive-value/wealthbox-cli/ci.yml?label=CI)](https://github.com/massive-value/wealthbox-cli/actions/workflows/ci.yml) [![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

> Unofficial, community-built. Not affiliated with or endorsed by Wealthbox.

------------------------------------------------------------------------

## Install (60 seconds, no Python required)

| Platform | Paste this into your terminal |
|---|---|
| **Mac / Linux** | `curl -LsSf https://raw.githubusercontent.com/massive-value/wealthbox-cli/main/scripts/install.sh \| bash` |
| **Windows** (PowerShell) | `irm https://raw.githubusercontent.com/massive-value/wealthbox-cli/main/scripts/install.ps1 \| iex` |

The installer:
1. Sets up the tools it needs (Python, etc. — handled automatically).
2. Asks for your **Wealthbox API token**. *Where to find it:* in Wealthbox, click your initials in the top right → **Settings** → **API Access** → **Create Access Token**. Paste the token when prompted.
3. Installs the AI agent skill into [Claude Code](https://claude.ai/download) (and Codex, if you have it).

That's it. Open Claude Code and try one of the prompts below.

------------------------------------------------------------------------

## Try this in Claude Code

```
"Show me my contacts created this week."

"Add Jane Doe as a new prospect — she came in as a referral from Bob Smith."

"Pull up the Smith household, add a task for me to call them on Monday."

"Find notes from my meeting with the Joneses last month and summarize the action items."

"Schedule an annual review with Mary Chen for the second Tuesday of next month."
```

The first time you ask the agent to do something, it'll walk you through a short Q&A about your firm's conventions (default contact types, naming patterns, common workflows). After that, it just works.

If you're new to Claude Code itself, [download it here](https://claude.ai/download) — it's free for personal use.

------------------------------------------------------------------------

## What it covers

Full read/write access for **contacts** (people, households, organizations, trusts), **tasks**, **events**, **notes**, **opportunities**, **projects**, and **workflows**. Read access for users, activity, and your firm's category lookups.

Anything you can do in Wealthbox manually, the agent can do for you — usually in one sentence.

------------------------------------------------------------------------

## How it works

Your AI agent uses a small command-line tool called `wbox` to talk to the [Wealthbox CRM API](https://dev.wealthbox.com). The skill that ships with this repo teaches the agent two things:

1. **Your firm's conventions** — the agent walks you through a one-time Q&A on first use ("what's your default contact type for new prospects? what's your household naming convention?"), then remembers your answers. Stored locally on your machine, never sent to a server.
2. **The right command for each request** — translating "add Jane as a prospect" into the correct API call, handling required fields, validating dropdowns against your firm's actual categories.

You stay in control: the agent shows you what it's about to do before it does it.

------------------------------------------------------------------------

## Already a Claude Code user?

You can install the skill directly from the plugin marketplace inside Claude Code:

```
/plugin marketplace add massive-value/wealthbox-cli
/plugin install wealthbox-crm@massive-value
```

The plugin auto-updates daily. Firm data lives at `~/.config/wbox/firm/` (Mac/Linux) or `%APPDATA%\wbox\firm\` (Windows) and survives plugin updates. Run `wbox doctor` to see your install status anytime.

------------------------------------------------------------------------

## For developers and power users

<details>
<summary><b>Direct CLI use, scripting, automation</b></summary>

```bash
pip install wealthbox-cli
wbox config set-token

# List contacts as a table
wbox contacts list --format table

# Create a contact
wbox contacts add person --first-name Jane --last-name Doe --contact-type Client

# Export tasks to CSV
wbox tasks list --format csv > tasks.csv

# Add a meeting note linked to a contact
wbox notes add "Discussed retirement plan" --contact 12345
```

Full command reference: [CLI Reference](https://massive-value.github.io/wealthbox-cli/cli-reference/). Output formats: `json` (default), `table`, `csv`, `tsv`. Date format: ISO 8601 (`2026-05-01T10:00:00-07:00`). See [Getting Started](https://massive-value.github.io/wealthbox-cli/getting-started/) for pipx, env-var auth, and project-scoped installs.
</details>

<details>
<summary><b>Manage skill installs (legacy / Codex / project scope)</b></summary>

```bash
wbox skills install        # interactive picker — Claude Code, Codex, project scope
wbox skills bootstrap      # populate firm data from your Wealthbox account
wbox skills refresh        # re-fetch generated firm data (categories, users, custom fields)
wbox skills upgrade        # update the bundled SKILL.md / references in every install
wbox skills firm-path      # print the canonical firm data directory
wbox skills uninstall      # remove the skill template (firm data is preserved)
wbox doctor                # comprehensive health check
```

The marketplace plugin path (above) is recommended for Claude Code. The legacy `wbox skills install` path remains for Codex users (until OpenAI's marketplace lands), project-scoped installs, or air-gapped setups without the `claude` CLI.
</details>

<details>
<summary><b>Architecture and contributing</b></summary>

```
src/wealthbox_tools/
    cli/        # Typer commands
    client/     # Async HTTP client built from mixins
    models/     # Pydantic v2 input validation
```

Built with [Typer](https://typer.tiangolo.com/), [httpx](https://www.python-httpx.org/), and [Pydantic v2](https://docs.pydantic.dev/).

```bash
git clone https://github.com/massive-value/wealthbox-cli
cd wealthbox-cli
python -m venv .venv
# Activate: source .venv/bin/activate (Mac/Linux) | .venv\Scripts\Activate.ps1 (Windows)
pip install -e ".[dev]"
pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CLAUDE.md](CLAUDE.md) for the architecture guide and conventions.
</details>

<details>
<summary><b>Troubleshooting</b></summary>

- **401 Unauthorized** — token expired or wrong. Run `wbox config show` to see the masked token, `wbox config set-token` to update.
- **Windows: "execution policy" error during install** — the installer offers to fix this for you. If you skipped it, run `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` and re-run the installer.
- **Linux: command not found after install** — open a new terminal, or run `source ~/.local/bin/env` in your current shell.
- **Date format errors** — Wealthbox needs ISO 8601: `"2026-05-01T10:00:00-07:00"` for datetimes, `"YYYY-MM-DD"` for date-only fields.
- **Writes succeed but nothing changes** — some category-constrained fields silently no-op on bad values. Check valid values with `wbox categories <type>`.

For anything else, open an issue at [github.com/massive-value/wealthbox-cli/issues](https://github.com/massive-value/wealthbox-cli/issues).
</details>

------------------------------------------------------------------------

## Links

[Documentation](https://massive-value.github.io/wealthbox-cli/) · [Changelog](https://massive-value.github.io/wealthbox-cli/changelog/) · [PyPI](https://pypi.org/project/wealthbox-cli/) · [Wealthbox CRM](https://www.wealthbox.com/) · [Wealthbox API](https://dev.wealthbox.com)

## Disclaimer

This is an **unofficial, community-built** tool. It is not affiliated with, endorsed by, or supported by Wealthbox or its parent company. "Wealthbox" is a trademark of its respective owner. Use of this tool is subject to the [Wealthbox API Terms of Service](https://dev.wealthbox.com).

## License

Apache 2.0 — see [LICENSE](LICENSE).
