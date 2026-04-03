# Wealthbox CLI — Command-Line Client for the Wealthbox CRM API

**wealthbox-cli** (`wbox`) is a command-line tool and Python client library for the [Wealthbox CRM](https://www.wealthbox.com/) API. It gives financial advisors, developers, and RIA firms full CRUD access to contacts, tasks, events, notes, households, and more — directly from the terminal.

[Get Started](getting-started.md){ .md-button .md-button--primary }
[CLI Reference](cli-reference.md){ .md-button }
[View on PyPI](https://pypi.org/project/wealthbox-cli/){ .md-button }

---

## Why Use wealthbox-cli?

- **No coding required** — structured CLI flags replace raw JSON and cURL commands
- **Automate CRM workflows** — script bulk updates, data exports, and scheduled tasks
- **Multiple output formats** — pipe JSON, CSV, or TSV directly to files or other tools
- **Built for financial advisors and developers** — covers contacts, households, tasks, events, notes, categories, and custom fields
- **Open source** — Apache 2.0 licensed, community-driven, and extensible

## Quick Install

```bash
pip install wealthbox-cli
```

Or with [pipx](https://pipx.pypa.io/) (recommended on Ubuntu/Debian):

```bash
pipx install wealthbox-cli
```

## Quick Example

```bash
# Store your API token
wbox config set-token

# List your contacts
wbox contacts list --format table

# Create a new contact
wbox contacts add person --first-name Jane --last-name Doe --contact-type Client

# Export tasks to CSV
wbox tasks list --format csv > tasks.csv
```

## Supported Wealthbox CRM Resources

| Resource | List | Get | Create | Update | Delete |
|----------|------|-----|--------|--------|--------|
| Contacts | Yes | Yes | Yes | Yes | Yes |
| Households | Yes | Yes | Yes | Yes | Yes |
| Tasks | Yes | Yes | Yes | Yes | Yes |
| Events | Yes | Yes | Yes | Yes | Yes |
| Notes | Yes | Yes | Yes | Yes | — |
| Users | Yes | — | — | — | — |
| Activity | Yes | — | — | — | — |
| Categories | Yes | — | — | — | — |

## Built With

- [Typer](https://typer.tiangolo.com/) — CLI framework
- [httpx](https://www.python-httpx.org/) — async HTTP client
- [Pydantic v2](https://docs.pydantic.dev/) — input validation
- [Wealthbox API](https://dev.wealthbox.com) — official API docs

## Links

- [GitHub Repository](https://github.com/massive-value/wealthbox-cli)
- [PyPI Package](https://pypi.org/project/wealthbox-cli/)
- [Wealthbox API Documentation](https://dev.wealthbox.com)
- [Changelog](changelog.md)

!!! note "Disclaimer"
    This is an unofficial, community-built tool. It is not affiliated with, endorsed by,
    or supported by Wealthbox or its parent company. "Wealthbox" is a trademark of its
    respective owner.
