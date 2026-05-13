# Changelog

All notable changes to `wealthbox-cli` are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.1] - 2026-05-13

Bug-fix release. `wbox self upgrade` was silently no-op'ing for users who
installed `wbox` via `uv tool install` or `pipx`: it computed the install root
from `sys.executable` (the venv's `python.exe`) and tried to swap the
console-script shim there, but `~/.local/bin/wbox.exe` (or pipx's equivalent)
is a separate copy uv/pipx made — replacing the venv-side shim never changed
what `PATH` resolved.

### Fixed
- `wbox self upgrade` now detects the install kind (`bundle` / `uv-tool` /
  `pipx` / `pip`) up front. Non-bundle installs exit `1` with the correct
  follow-up command (`uv tool upgrade wealthbox-cli`, `pipx upgrade
  wealthbox-cli`, or `pip install --upgrade wealthbox-cli`) instead of
  scheduling a swap that would never take effect on `PATH`.

## [2.2.0] - 2026-05-13

Small feature + correctness release. Disambiguates the two IDs returned by
`wbox me`, fixes a silent truncation in `wbox users list` on large firms, and
clears Node 20 deprecation warnings from CI ahead of GitHub's June 2026 cutoff.

### Added
- `wbox me user-id` — prints `current_user.id` (the workspace user ID accepted
  by `--assigned-to`) as a bare integer, for composing with command
  substitution: `wbox tasks list --assigned-to "$(wbox me user-id)"` (#90, #91).
- `wbox me --format table` now labels the two IDs as `login_id` and
  `user_id (--assigned-to)` so they aren't confusable at a glance. The JSON
  shape is unchanged — no breaking change for existing scripts (#91).
- Skill docs (`lookups.md`, `tasks.md`, `contacts.md`) flag the two-ID trap
  inline near `--assigned-to`.

### Fixed
- `wbox users list` now paginates across all pages. Previously, firms with
  more than 25 users silently saw a truncated list — the CLI exposes no
  `--page` flag, so there was no manual workaround.
- mkdocs docs deploy was failing on every main push because `docs/index.md`
  linked to a missing `changelog.md`. `CHANGELOG.md` is now staged into
  `docs/` at build time and listed in nav (#92).

### Changed
- CI actions bumped to Node 24 runtimes ahead of GitHub's June 2 2026 cutoff:
  `actions/checkout` v4→v6, `astral-sh/setup-uv` v6→v8.1.0 (pinned exact —
  setup-uv v8+ no longer publishes rolling major tags as a supply-chain
  mitigation), `actions/setup-python` v5→v6, `actions/deploy-pages` v4→v5,
  `actions/upload-pages-artifact` v3→v5 (#92, #93).

## [2.1.0] - 2026-05-09

Repository simplification release. Drops a runtime dep, retires `.env` support,
and switches dev tooling to [uv](https://docs.astral.sh/uv/).

### Breaking
- **Removed `.env` file support.** Token resolution is now a 3-tier chain:
  `--token` flag → `WEALTHBOX_TOKEN` env var → config file. Users relying on a
  working-directory `.env` should migrate to `wbox config set-token` (preferred)
  or export `WEALTHBOX_TOKEN` in their shell. The `python-dotenv` runtime
  dependency was dropped.

### Changed
- Development tooling moved to [uv](https://docs.astral.sh/uv/). `uv sync
  --extra dev` replaces the manual `python -m venv` + activate + `pip install
  -e` dance, and `uv run wbox …` replaces direct `.venv/bin/wbox` invocation.
  CI now uses `astral-sh/setup-uv@v6` and `uv build` for the publish job. Plain
  `pip install -e ".[dev]"` continues to work — `pyproject.toml` is the source
  of truth for both tools.
- `scripts/run-wbox.sh` and `scripts/smoke_test.sh` invoke via `uv run` and no
  longer source a `.env` file.

### Removed
- `.env` and `.env.example` files at the repo root.
- `.python-version` file. `requires-python = ">=3.11"` in `pyproject.toml` is
  the authoritative interpreter constraint; uv reads it directly.

## [2.0.0] - 2026-05-09

v2 retires the Claude marketplace plugin distribution and ships `wbox` as a
standalone binary plus a PyPI package. Existing v1 users must reinstall via the
new bootstrap script or `pip install wealthbox-cli` — see Breaking below.

### Breaking
- **Retired the Claude marketplace plugin distribution.** `wbox` no longer
  ships through the Claude marketplace. Install via `pip install wealthbox-cli`
  or the bootstrap script (`curl -fsSL https://github.com/massive-value/wealthbox-cli/releases/latest/download/install.sh | sh`).
  v1's `claude plugin install` flow is gone.
- **Rewrote `install.sh` and `install.ps1`** to fetch a prebuilt binary from
  GitHub Releases instead of detecting and preferring the Claude marketplace
  plugin (#42, #43). The installers now verify a checksum manifest before
  swapping the binary into place.
- **Removed v1 distribution artifacts** — the in-repo plugin manifest and
  marketplace metadata are deleted (#27).
- **Dropped plugin-cache scanning** from the skill platform helpers; `wbox
  doctor` and `wbox skills list` no longer probe Claude's plugin cache (#28).

### Added
- `wbox firm export` — end-to-end export of the configured firm's CRM data to
  a portable JSON snapshot (#31).
- `wbox firm import` with `--mode overwrite|merge|abort-on-conflict` and
  `--from-url` for fetching a snapshot directly from a URL (#36, #46, #45).
- `wbox firm diff` — diff a local snapshot against the live firm to preview
  what an import would change (#47).
- Post-import provenance metadata and a 90-day freshness warning surfaced by
  `wbox doctor` (#48).
- `wbox doctor` promoted to a top-level command, with a warning when the local
  install is more than 30 days behind the latest GitHub release (#41).
- `wbox self upgrade` — happy-path binary self-update (#32), Windows
  deferred-swap support (#67), and a subprocess hand-off so a fresh `wbox`
  upgrades bundled skills after the binary swap (#40).
- `wbox prefs` — user-preferences slot for per-user defaults (#29).
- Per-platform PyInstaller build + release workflow that publishes Linux,
  macOS, and Windows binaries plus a checksum manifest to GitHub Releases (#33).
- Skill-reference auto-generation markers across the bundled skill (#30, #85)
  and a CI drift-detection job that fails when generated skill blocks fall out
  of sync (#86).
- Bootstrap Q&A skips the onboarding prompts when an imported firm snapshot
  already carries an `onboarded_at` timestamp (#49).
- `wbox firm apply` and `wbox doctor` now sweep stale `.old.<ts>` backup files
  left behind by interrupted upgrades (#39).

### Changed
- Rewrote the README around the v2 install flow — bootstrap script first, PyPI
  second, no marketplace path (#83).
- Documented the three-layer config resolution (flag > env > config file) and
  the new `prefs` commands inside the bundled skill (#34).

### Fixed
- `wbox self upgrade` now reads the checksum manifest under its release-asset
  filename, fixing the post-#33 break (#82).
- Pytest no longer clobbers the developer's real `~/.wbox_rate_limit.json`;
  the rate-limit state file is isolated per test session (#56).

## [1.3.0](https://github.com/massive-value/wealthbox-cli/releases/tag/v1.3.0) - 2026-05-03

### Added

- **`wbox doctor`** — comprehensive top-level health check at the CLI root. Reports the wbox CLI version + Python version + binary location; authentication source detection (flag / env var / config file / `.env`) plus a smoke test against `/me`; agent CLI presence (`claude` / `codex` on PATH); legacy skill installs; plugin installs (managed via `claude plugin install` / `codex plugin install`); firm data state with file count, generated-vs-hand-edited split, and oldest-generated-file timestamp; and a Summary section listing actionable issues. `wbox skills doctor` keeps working as an alias of the new top-level command — both call the same function so output never drifts.
- `wbox skills list` and `wbox skills doctor` now detect plugin-installed copies of `wealthbox-crm` under `~/.claude/plugins/cache/.../skills/wealthbox-crm/` and `~/.codex/plugins/cache/.../skills/wealthbox-crm/`. Previously a user who installed via the marketplace plugin path saw "not installed" everywhere even though the plugin was actively serving the skill.
- Bootstrap installer (`scripts/install.sh` / `scripts/install.ps1`) now prefers the Claude Code plugin marketplace path when `claude` is on PATH — runs `claude plugin marketplace add` + `claude plugin install` directly, then offers a separate Codex install. Falls back to the legacy `wbox skills install` picker when no `claude` CLI is detected.
- Bootstrap installer pre-flight checks Windows PowerShell `ExecutionPolicy` and offers to set `RemoteSigned` for the current user if needed (no admin required), instead of bombing partway through with Astral's terse error.

### Fixed

- Bootstrap `install.sh` no longer hangs at startup. The previous version did `exec </dev/tty` at the top, which cut off bash's source of piped script content (`curl … | bash`) and waited forever for the rest of the script to arrive on the user's keyboard. The whole body is now wrapped in a `main()` function so bash reads it fully before executing.
- Bootstrap `install.ps1` no longer auto-closes its window on error. Wrapped in try/catch/finally with explicit step headers and a "Press Enter to close" pause so a transient PowerShell host stays open long enough to show the actual error.

## [1.2.0](https://github.com/massive-value/wealthbox-cli/releases/tag/v1.2.0) - 2026-05-02

### Changed

- **Firm data hoisted to a canonical machine-level path.** `firm/` and the firm metadata (`identity`, `files` timestamps, `onboarded_at`) now live at `~/.config/wbox/firm/` (macOS/Linux) or `%APPDATA%\wbox\firm\` (Windows) — one source of truth per machine. Previously each skill install had its own `firm/` and embedded the firm section in `<skill_dir>/_meta.json`. The new layout survives plugin auto-updates, skill template upgrades, and reinstalls without risking the firm bootstrap state being wiped, and removes the duplication problem when the same skill is installed via multiple paths (Claude Code marketplace + manual install + Codex). Per-install `_meta.json` is retained for the per-install `template.cli_version` field.
- `SKILL.md` now instructs the agent to run `wbox skills firm-path` to find the firm directory, then read `<firm>/<resource>.md` files from there. `bootstrap.md` updated to match.

### Added

- `wbox skills firm-path` — prints the canonical firm directory. Used by the agent to locate firm data, and useful for ad-hoc inspection.
- Automatic migration: any command that reads firm state (`bootstrap`, `refresh`, `doctor`, `list`, `mark-onboarded`, `firm-path`) detects legacy `<skill_dir>/firm/` and `<skill_dir>/_meta.json.firm` data on first run and moves it to the canonical path. If multiple installs have legacy data, the one with the most recent `onboarded_at` (or generated-files timestamp) wins.
- **Claude Code plugin marketplace.** `.claude-plugin/marketplace.json` at the repo root, plus a self-contained plugin at `plugins/wealthbox-crm/` with `.claude-plugin/plugin.json`. Users can now install with `/plugin marketplace add massive-value/wealthbox-cli` then `/plugin install wealthbox-crm@massive-value` directly inside Claude Code. The custom marketplace works immediately; an Anthropic official-marketplace submission is in flight.
- **Codex plugin manifest** at `.codex-plugin/plugin.json` plus a `codex-skill/` mirror of the skill template, ready for the openai/skills PR and a future Codex marketplace listing once self-serve publishing opens.
- `scripts/sync-plugin.py` — keeps the plugin and codex copies in sync with the canonical skill template at `src/wealthbox_tools/skills/wealthbox-crm/`. Run before committing skill template changes.

### Removed

- `wbox skills sync` is gone. Firm data is now machine-level, so there's nothing to sync between platform installs.

### Deprecated

- `--platform` flag on `bootstrap`, `refresh`, and `mark-onboarded` is accepted but ignored, with a warning. Firm operations are no longer scoped per platform.

## [1.1.6](https://github.com/massive-value/wealthbox-cli/releases/tag/v1.1.6) - 2026-05-01

### Fixed
- `wbox skills bootstrap` and `wbox skills refresh` now paginate every API call. Previously they fetched a single page (default `per_page=25`) for each category type, custom-field document type, and the user list, silently truncating any workspace with more than 25 entries per group. Generated `firm/categories.md`, `firm/custom-fields.md`, and `firm/users.md` are now complete.
- The codex skill installs as `SKILL.md`, not `AGENTS.md`. Codex uses `SKILL.md` for skills (same as Claude Code); `AGENTS.md` is the project-level instructions file (the codex equivalent of `CLAUDE.md`) and was never the right name for a skill. **Migration:** if you installed the skill under codex on 1.1.5 or earlier, reinstall with `wbox skills install --platform codex --force` to drop the stale `AGENTS.md`.
- The skill's First Run check now keys on `firm.onboarded_at` instead of the mere presence of a `firm` section. Previously, running `wbox skills bootstrap` populated the `firm` section, which made the agent skip the qualitative Q&A in `bootstrap.md` on first invocation. The CLI bootstrap is the *quantitative* half (categories, custom fields, users); the *qualitative* half (firm defaults, naming conventions, named workflows) happens at first agent invocation, and the agent now stamps `firm.onboarded_at` when it finishes.

### Added
- `wbox skills mark-onboarded` — stamps `firm.onboarded_at` in the skill's `_meta.json`. The agent invokes this as the last step of `bootstrap.md`; users typically don't need to run it manually.
- `wbox skills list` and `wbox skills doctor` now report onboarded status (`bootstrapped (qualitative pending)` vs `onboarded`).

## [1.1.5](https://github.com/massive-value/wealthbox-cli/releases/tag/v1.1.5) - 2026-05-01

### Fixed
- `wbox skills install`, `wbox skills bootstrap`, and `wbox skills refresh` now honor every token source the rest of the CLI does. Previously these commands only looked at the `--token` flag and `WEALTHBOX_TOKEN` env var, ignoring tokens stored via `wbox config set-token` and `.env` files. Users running `wbox skills install` after `wbox config set-token` saw "Wealthbox token required" errors despite having a token set.
- The "token required" error message now lists every supported source (flag, env var, config file, `.env`).

### Added
- `wbox skills install` accepts `--token` (matching `bootstrap`, `refresh`, and `doctor`), so a token can be supplied inline for the post-install bootstrap step.

## [1.1.4](https://github.com/massive-value/wealthbox-cli/releases/tag/v1.1.4) - 2026-05-01

### Added
- Workspace-level aliases for every resource-scoped category lookup. `wbox categories contact-types`, `wbox categories contact-roles`, `wbox categories event-categories`, `wbox categories task-categories`, and the rest now work alongside their existing `wbox <resource> categories` forms. Both routes call the same API endpoint.

### Docs
- Skill references (`lookups.md`, `contacts.md`) and `docs/cli-reference.md` updated to surface the workspace-level form as the primary listing.

## [1.0.2](https://github.com/massive-value/wealthbox-cli/releases/tag/v1.0.2) - 2026-03-30

### Changed
- Redesigned comment handling — comments are now embedded in `get` commands
- Added ID shorthand for resource lookups

## [1.0.1](https://github.com/massive-value/wealthbox-cli/releases/tag/v1.0.1) - 2026-03-30

### Changed
- Updated README with API token instructions and config commands
- Added deploy workflow documentation

## [1.0.0](https://github.com/massive-value/wealthbox-cli/releases/tag/v1.0.0) - 2026-03-29

### Added
- Full CRUD for contacts (person, household, organization, trust), tasks, events, and notes
- Household member management (`add-member`, `remove-member`)
- Read/list access for users, activity, `me`, and categories
- Type-specific contact creation subcommands: `contacts add person|household|org|trust`
- `--more-fields` escape hatch for uncommon JSON fields on contacts, tasks, projects, opportunities, and workflows
- Multiple output formats: `json`, `table`, `csv`, `tsv` via `--format`
- Nested field flattening for tabular output (linked_to, email_addresses, tags, etc.)
- Client-side filtering for fields the API doesn't support server-side (e.g. `--assigned-to` on contacts)
- Category and custom field lookups (resource-scoped and workspace-level)
- Token management via `wbox config set-token|show|clear`
- Authentication via `--token` flag, `WEALTHBOX_TOKEN` env var, config file, or `.env`
- Sliding-window rate limiter (300 req / 5-min window) with automatic retry on 429
- GitHub Actions CI (lint + test across Python 3.11, 3.12, 3.13)
- PyPI publishing via trusted publishers (OIDC)

## [0.8.5](https://github.com/massive-value/wealthbox-cli/releases/tag/v0.8.5)

### Changed
- Standardized CLI help text across all commands

## [0.8.4](https://github.com/massive-value/wealthbox-cli/releases/tag/v0.8.4)

### Added
- PyPI badges and install instructions

## [0.8.0](https://github.com/massive-value/wealthbox-cli/releases/tag/v0.8.0)

### Added
- Events CRUD support
- Notes CRUD support (create, read, update — delete not supported by API)

## [0.7.0](https://github.com/massive-value/wealthbox-cli/releases/tag/v0.7.0)

### Added
- Tasks CRUD support
- Task categories

## [0.6.0](https://github.com/massive-value/wealthbox-cli/releases/tag/v0.6.0)

### Added
- Household member management commands

## [0.5.0](https://github.com/massive-value/wealthbox-cli/releases/tag/v0.5.0)

### Added
- Contact CRUD operations
- Contact categories and metadata lookups

## [0.4.0](https://github.com/massive-value/wealthbox-cli/releases/tag/v0.4.0)

### Added
- Output format support (`--format json|table|csv|tsv`)

## [0.3.0](https://github.com/massive-value/wealthbox-cli/releases/tag/v0.3.0)

### Added
- User listing and `me` command
- Activity feed with cursor-based pagination

## [0.2.0](https://github.com/massive-value/wealthbox-cli/releases/tag/v0.2.0)

### Added
- Rate limiting (sliding-window, 300 req / 5-min)
- Token configuration (`--token`, env var, `.env`)

## [0.1.0](https://github.com/massive-value/wealthbox-cli/releases/tag/v0.1.0)

### Added
- Initial release — basic Wealthbox API client with CLI scaffolding
