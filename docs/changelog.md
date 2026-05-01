# Changelog

All notable changes to **wealthbox-cli** are documented here.

This project uses [Semantic Versioning](https://semver.org/).

---

## [1.1.6](https://github.com/massive-value/wealthbox-cli/releases/tag/v1.1.6) — 2026-05-01

### Fixed
- `wbox skills bootstrap` and `wbox skills refresh` now paginate every API call. Previously they fetched a single page (default `per_page=25`) for each category type, custom-field document type, and the user list, silently truncating any workspace with more than 25 entries per group. Generated `firm/categories.md`, `firm/custom-fields.md`, and `firm/users.md` are now complete.
- The codex skill installs as `SKILL.md`, not `AGENTS.md`. Codex uses `SKILL.md` for skills (same as Claude Code); `AGENTS.md` is the project-level instructions file (the codex equivalent of `CLAUDE.md`) and was never the right name for a skill. **Migration:** if you installed the skill under codex on 1.1.5 or earlier, reinstall with `wbox skills install --platform codex --force` to drop the stale `AGENTS.md`.
- The skill's First Run check now keys on `firm.onboarded_at` instead of the mere presence of a `firm` section. Previously, running `wbox skills bootstrap` populated the `firm` section, which made the agent skip the qualitative Q&A in `bootstrap.md` on first invocation. The CLI bootstrap is the *quantitative* half (categories, custom fields, users); the *qualitative* half (firm defaults, naming conventions, named workflows) happens at first agent invocation, and the agent now stamps `firm.onboarded_at` when it finishes.

### Added
- `wbox skills mark-onboarded` — stamps `firm.onboarded_at` in the skill's `_meta.json`. The agent invokes this as the last step of `bootstrap.md`; users typically don't need to run it manually.
- `wbox skills list` and `wbox skills doctor` now report onboarded status (`bootstrapped (qualitative pending)` vs `onboarded`).

---

## [1.1.5](https://github.com/massive-value/wealthbox-cli/releases/tag/v1.1.5) — 2026-05-01

### Fixed
- `wbox skills install`, `wbox skills bootstrap`, and `wbox skills refresh` now honor every token source the rest of the CLI does. Previously these commands only looked at the `--token` flag and `WEALTHBOX_TOKEN` env var, ignoring tokens stored via `wbox config set-token` and `.env` files. Users running `wbox skills install` after `wbox config set-token` saw "Wealthbox token required" errors despite having a token set.
- The "token required" error message now lists every supported source (flag, env var, config file, `.env`).

### Added
- `wbox skills install` accepts `--token` (matching `bootstrap`, `refresh`, and `doctor`), so a token can be supplied inline for the post-install bootstrap step.

---

## [1.1.4](https://github.com/massive-value/wealthbox-cli/releases/tag/v1.1.4) — 2026-05-01

### Added
- Workspace-level aliases for every resource-scoped category lookup. `wbox categories contact-types`, `wbox categories contact-roles`, `wbox categories event-categories`, `wbox categories task-categories`, and the rest now work alongside their existing `wbox <resource> categories` forms. Both routes call the same API endpoint.

### Docs
- Skill references (`lookups.md`, `contacts.md`) and `docs/cli-reference.md` updated to surface the workspace-level form as the primary listing.

---

## [1.0.2](https://github.com/massive-value/wealthbox-cli/releases/tag/v1.0.2) — 2026-03-30

### Changed
- Redesigned comment handling — comments are now embedded in `get` commands
- Added ID shorthand for resource lookups

---

## [1.0.1](https://github.com/massive-value/wealthbox-cli/releases/tag/v1.0.1) — 2026-03-30

### Changed
- Updated README with API token instructions and config commands
- Added deploy workflow documentation

---

## [1.0.0](https://github.com/massive-value/wealthbox-cli/releases/tag/v1.0.0) — 2026-03-29

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

---

## [0.8.5](https://github.com/massive-value/wealthbox-cli/releases/tag/v0.8.5)

### Changed
- Standardized CLI help text across all commands

---

## [0.8.4](https://github.com/massive-value/wealthbox-cli/releases/tag/v0.8.4)

### Added
- PyPI badges and install instructions

---

## [0.8.0](https://github.com/massive-value/wealthbox-cli/releases/tag/v0.8.0)

### Added
- Events CRUD support
- Notes CRUD support (create, read, update — delete not supported by API)

---

## [0.7.0](https://github.com/massive-value/wealthbox-cli/releases/tag/v0.7.0)

### Added
- Tasks CRUD support
- Task categories

---

## [0.6.0](https://github.com/massive-value/wealthbox-cli/releases/tag/v0.6.0)

### Added
- Household member management commands

---

## [0.5.0](https://github.com/massive-value/wealthbox-cli/releases/tag/v0.5.0)

### Added
- Contact CRUD operations
- Contact categories and metadata lookups

---

## [0.4.0](https://github.com/massive-value/wealthbox-cli/releases/tag/v0.4.0)

### Added
- Output format support (`--format json|table|csv|tsv`)

---

## [0.3.0](https://github.com/massive-value/wealthbox-cli/releases/tag/v0.3.0)

### Added
- User listing and `me` command
- Activity feed with cursor-based pagination

---

## [0.2.0](https://github.com/massive-value/wealthbox-cli/releases/tag/v0.2.0)

### Added
- Rate limiting (sliding-window, 300 req / 5-min)
- Token configuration (`--token`, env var, `.env`)

---

## [0.1.0](https://github.com/massive-value/wealthbox-cli/releases/tag/v0.1.0)

### Added
- Initial release — basic Wealthbox API client with CLI scaffolding
