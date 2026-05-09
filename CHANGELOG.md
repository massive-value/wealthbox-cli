# Changelog

All notable changes to `wealthbox-cli` are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
