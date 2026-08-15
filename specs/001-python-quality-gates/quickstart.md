# Quickstart: Python Quality Gates

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md) ·
Contract: [contracts/quality-command.md](./contracts/quality-command.md)

This guide validates the quality-gate suite end-to-end. It assumes the implementation tasks
(`/speckit-tasks` → `/speckit-implement`) have produced `pyproject.toml`, `uv.lock`, the src/tests
scaffold, and the CI workflow.

## Prerequisites

- Python 3.12 or newer available on the machine.
- **uv** installed (the package/environment manager). If missing, install per uv's official docs.

## Setup

```bash
# From the repository root — creates the locked environment with all quality tools
uv sync
```

This installs ruff, pylint, bandit, ty, pytest, and poethepoet exactly as pinned in `uv.lock`.

## Validation scenarios

### Scenario 1 — Clean codebase passes (Acceptance US1-1)

```bash
uv run poe check
```

**Expected**: every gate (format, lint, security, types, tests) reports success; the command exits
`0`.

### Scenario 2 — All four defect categories are caught in one run (SC-003, US1-2)

Run the gate self-test, which points the gates at `tests/fixtures/bad_example.py`:

```bash
uv run poe test -k gate_selftest      # or: uv run pytest -k gate_selftest
```

**Expected**: the test passes because the suite reports at least one finding in each category —
style/format, likely-bug, hard-coded secret, and type error — each attributed to its gate with file
and line.

### Scenario 3 — Any single failure fails the aggregate (FR-002, US1)

Temporarily introduce one violation into a real file under `src/` (e.g. an unused import), then:

```bash
uv run poe check
```

**Expected**: the offending gate reports the finding with file+line, other gates still run, and the
overall command exits non-zero. Revert the change afterward.

### Scenario 4 — Auto-fix the mechanical subset

```bash
uv run poe fix        # applies ruff format + ruff --fix
uv run poe check      # now green for the auto-fixable issues
```

### Scenario 5 — Individual gates run independently (FR-004)

```bash
uv run poe lint
uv run poe security
uv run poe types
uv run poe test
```

**Expected**: each runs on its own and returns its own verdict.

### Scenario 6 — Reasoned suppression silences one finding only (FR-009/SC-007)

Add an inline suppression with a justification comment (e.g. `# noqa: <rule>  # reason: …`) to a
single line that has a known false positive.

**Expected**: only that one finding is silenced; the same rule still fires elsewhere; ruff `RUF100`
flags the suppression if it later becomes unused.

### Scenario 7 — CI parity (FR-006/SC-005)

Open a pull request against `main`.

**Expected**: the `quality` GitHub Actions job runs `uv run poe check` and produces the same verdict
as local; a failing check blocks merge, a passing check does not.

## Success signals

- `uv run poe check` is the single command that surfaces all findings (SC-001).
- Full local run completes in under ~30s on the current codebase (SC-004).
- Merged changes to `main` have all passed the gates via the required CI check (SC-002).
- All tool configuration is readable in one file, `pyproject.toml` (SC-006).
