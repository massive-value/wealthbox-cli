# Getting Started with Wealthbox CLI

This guide walks you through installing **wealthbox-cli** and configuring it to connect to your Wealthbox CRM account.

---

## Installation

### One-line installer (no Python required)

If you don't have Python installed, the bootstrap script handles everything: it installs [uv](https://github.com/astral-sh/uv) (which provisions Python automatically), installs `wbox`, prompts for your API token, and offers to install the AI agent skill.

=== "macOS / Linux"

    ```bash
    curl -LsSf https://raw.githubusercontent.com/massive-value/wealthbox-cli/main/scripts/install.sh | bash
    ```

=== "Windows (PowerShell)"

    ```powershell
    irm https://raw.githubusercontent.com/massive-value/wealthbox-cli/main/scripts/install.ps1 | iex
    ```

### From PyPI (recommended for Python users)

```bash
pip install wealthbox-cli
```

### With pipx (recommended for Ubuntu/Debian)

On systems where the system Python is externally managed (Ubuntu 23.04+, Debian 12+),
`pip install` outside a virtual environment is blocked by [PEP 668](https://peps.python.org/pep-0668/).
Use [pipx](https://pipx.pypa.io/) to install CLI tools in isolated environments:

```bash
pipx install wealthbox-cli
```

This puts `wbox` and `wb` on your PATH without touching system Python.

### From Source (development)

```bash
git clone https://github.com/massive-value/wealthbox-cli
cd wealthbox-cli
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# OR
.venv\Scripts\activate     # Windows
pip install -e ".[dev]"
```

---

## Getting Your Wealthbox API Token

1. Log in to [Wealthbox](https://app.crmworkspace.com)
2. Click the three dots menu (**...**) in the top right
3. Go to **Settings** → **API Access**
4. Click **Create Access Token**

---

## Storing Your Token

```bash
wbox config set-token
```

This prompts for your Wealthbox API token (input is masked) and stores it in
`~/.config/wbox/config.json` (Linux/macOS) or `%APPDATA%\wbox\config.json` (Windows).

Other configuration commands:

```bash
wbox config show     # display stored config (token masked)
wbox config clear    # remove stored config
```

### Alternative Authentication Methods

For CI, scripting, or containers:

=== "Environment variable"

    ```bash
    export WEALTHBOX_TOKEN="your_api_token_here"
    ```

=== ".env file"

    ```bash
    echo 'WEALTHBOX_TOKEN=your_api_token_here' > .env
    ```

=== "Per-command flag"

    ```bash
    wbox contacts list --token your_api_token_here
    ```

Token is resolved in this order: `--token` flag → `WEALTHBOX_TOKEN` env var → config file → `.env` file.

---

## Verify Your Setup

```bash
# Check your identity
wbox me

# List users in your workspace
wbox users list

# List your first contact
wbox contacts list --per-page 1
```

---

## Next Steps

- Browse the full [CLI Reference](cli-reference.md) for all commands and options
- See [Contributing](contributing.md) to help improve this tool
