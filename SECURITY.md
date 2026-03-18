# Security Policy

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Instead, email **dev.bluehorizon@gmail.com** with:

- A description of the vulnerability
- Steps to reproduce
- Potential impact

You will receive a response within 5 business days. If the issue is confirmed, a fix will be prioritized and you will be credited in the release notes (unless you prefer to remain anonymous).

## API Token Safety

Your Wealthbox API token grants access to your CRM data. Keep it safe:

- **Never commit your token to version control.** Use `.env` (already in `.gitignore`) — see `.env.example` for the correct pattern.
- **Never share your token** in issues, PRs, or chat.
- If a token is accidentally exposed, regenerate it immediately in your Wealthbox account settings.

## Scope

This tool is an unofficial CLI wrapper around the Wealthbox API. Security issues in the Wealthbox API itself should be reported directly to Wealthbox.
