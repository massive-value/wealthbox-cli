# v1.0.0 Release Design

**Date:** 2026-03-30
**Scope:** Bug fixes, CI/CD, PyPI publishing, version bump

---

## 1. Bug Fixes & Polish (Moderate Scope)

### High-Severity Fixes

- **JSON parse safety:** Wrap all `resp.json()` calls in client mixins with try-catch. Raise `WealthboxAPIError` with the status code and a clear message on parse failure (e.g., API returning HTML error pages).

- **TaskUpdateInput XOR validator:** Fix `validate_due_date_xor_frame()` to allow both `due_date` and `frame` to be unset in update payloads. The current XOR rule should only apply to `TaskCreateInput`; updates should allow partial field sets.

- **fetch_all_pages() robustness:** Add handling for missing or non-list `collection_key` in API responses. Raise `WealthboxAPIError` instead of silently returning empty results.

### Medium-Severity Fixes

- **Remove redundant min_length on datetime fields:** `EventCreateInput.starts_at` and `ends_at` have `min_length=1` alongside datetime validation — remove the redundant constraint.

- **ProjectCreateInput description:** Verify whether the API allows `description=None` on project creation. If so, make it optional.

- **Retry-After logging:** Add a log warning when `Retry-After` header is missing or malformed and the client falls back to the default 5.0s sleep.

### Help Text Cleanup

- Add missing `help=` parameter to ~4 options:
  - `workflows.py`: `resource_id` option
  - `tasks.py`: `assigned_to_team` option
  - `notes.py`: `order` option
  - `events.py`: `page` option (also add explicit flag name)

- Standardize all `@app.command()` help strings to imperative verb, capitalized:
  - "Returns a list of tasks..." → "List tasks..."

- Standardize all `typer.Option()` help text:
  - Capital first letter
  - No trailing period
  - Consistent phrasing patterns

### New Tests

- `fetch_all_pages()` edge cases: empty results, single page, missing collection key
- JSON parse failure in at least one client method (representative test)
- `TaskUpdateInput` accepts partial payloads without due_date/frame

---

## 2. CI/CD Pipeline

### Single workflow file: `.github/workflows/ci.yml`

**Triggers:**
- Push to `main`
- Pull requests to `main`
- Version tags (`v*`)

**Job: `lint`** (every trigger)
- Python 3.12
- `ruff check src/ tests/`
- `mypy src/` (only if it passes clean today; skip if existing errors)

**Job: `test`** (every trigger)
- Matrix: Python 3.11, 3.12, 3.13
- `pip install -e ".[dev]"`
- `pytest`

**Job: `publish`** (only on `v*` tags, requires lint + test to pass)
- `python -m build`
- Publish via `pypa/gh-action-pypi-publish` using trusted publishers (OIDC)
- No API tokens stored in GitHub secrets

### Pre-work

- Verify `ruff check` passes clean on current codebase
- Verify `mypy` status — include in CI only if it passes or we fix errors as part of this work

---

## 3. Packaging & PyPI Readiness

### pyproject.toml Changes

- **Rename package:** `wealthbox-tools` → `wealthbox-cli` (distribution name only; import path stays `wealthbox_tools`)
- **Add classifiers:**
  - `Programming Language :: Python :: 3.13`
  - `Environment :: Console`
  - `Intended Audience :: Developers`
- **Add URL:** `Repository = "https://github.com/massive-value/wealthbox-cli"` to `[project.urls]`

### README.md Updates

- Add badges: PyPI version, Python version support
- Add `pip install wealthbox-cli` as primary install method
- Keep git clone as secondary/development install

### sdist Cleanup

Configure hatch build excludes in pyproject.toml:
- `tests/`
- `resources/`
- `scripts/`
- `run-wbox.sh`
- `smoke_test.sh`
- `.python-version`

---

## 4. Version Bump & Release

**Final step** after all other work is complete:

1. Bump `pyproject.toml` version from `0.8.6` to `1.0.0`
2. Commit all changes
3. Tag `v1.0.0`
4. Push → CI runs → auto-publish to PyPI

### Pre-tag Checklist

- [ ] All tests pass (122+)
- [ ] Ruff clean
- [ ] `python -m build` succeeds
- [ ] Package installs correctly from built wheel
- [ ] PyPI trusted publisher configured on pypi.org for `massive-value/wealthbox-cli`

---

## Out of Scope

- Low-severity audit items (rate limiter file locking, LinkedToRef forward-compat, etc.)
- TestPyPI dry-run
- New feature work
- mypy error fixes (unless trivial)

---

## Completed 2026-03-31

All items shipped as v1.0.0 (then v1.0.1 docs patch). Additional work beyond original spec:

- **`wbox config` command** — `set-token`, `show`, `clear` for token management. Stores in platform config dir. Token resolution: flag > env var > config file > .env.
- **README updates** — API token setup instructions, PyPI badges, config command docs.
- **CLAUDE.md / CONTRIBUTING.md** — deploy workflow, CI info, config command docs.
- **PyPI trusted publisher** — configured with environment `pypi` (not blank).
