# Phase 1 Data Model: Python Quality Gates

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md)

This feature is configuration-and-process, not runtime data. The "entities" below are configuration
and result structures realized in `pyproject.toml`, CI, and the gate runner's output — not database
tables. They map the spec's Key Entities to concrete artifacts.

---

## Entity: Quality Gate

One category of automated check. Four instances exist.

| Field | Description |
|-------|-------------|
| `id` | Stable name: `format`, `lint`, `security`, `types`, `tests` |
| `tool` | Realizing tool: ruff (format+lint), pylint (lint), bandit (security), ty (types), pytest (tests) |
| `config_location` | `[tool.*]` table in `pyproject.toml` |
| `command` | The poe sub-task that runs it |
| `targets` | Paths scanned (`src/`, and `tests/` where applicable) |
| `result` | `pass` \| `fail` (derived from exit code) |
| `independent` | Always true — runs regardless of other gates' results (FR-004) |

**Instances**

| id | tool | pyproject table | targets |
|----|------|-----------------|---------|
| `format` | ruff format --check | `[tool.ruff]`, `[tool.ruff.format]` | `src/`, `tests/` |
| `lint` | ruff check (+ pylint) | `[tool.ruff.lint]`, `[tool.pylint]` | `src/`, `tests/` |
| `security` | bandit | `[tool.bandit]` | `src/` |
| `types` | ty | `[tool.ty]` | `src/` |
| `tests` | pytest | `[tool.pytest.ini_options]` | `tests/` |

**Validation rules**
- Every gate MUST inherit the Python 3.12 target from `requires-python` (directly or via
  `target-version = "py312"`).
- A gate whose tool is missing MUST fail loudly, never skip silently (FR-011).

---

## Entity: Finding

A single reported issue from a gate.

| Field | Description | Source |
|-------|-------------|--------|
| `gate` | Which gate raised it (`lint`, `security`, …) | runner attribution |
| `file` | Path to offending file | tool output |
| `line` | Line number | tool output |
| `rule_id` | Tool rule code (e.g. `B008`, `S105`, ty diagnostic id) | tool output |
| `message` | Human-readable description | tool output |
| `severity` | Tool-reported severity/confidence where available | tool output |

**Validation rules**
- Every finding MUST carry `gate`, `file`, `line` (FR-003).
- Findings from different gates on the same line remain separately attributed (Edge Cases).

---

## Entity: Gate Configuration

The single, version-controlled source of truth for what is enforced.

| Field | Description |
|-------|-------------|
| `location` | `pyproject.toml` (only) — no per-tool dotfiles |
| `python_floor` | `requires-python = ">=3.12"` |
| `line_length` | `120` — ruff `line-length` and pylint `max-line-length`, one shared value |
| `build_system` | `[build-system]` → hatchling backend |
| `enabled_rules` | Per-gate rule selection (ruff `lint.select`, pylint enable/disable, bandit, ty) |
| `runner_tasks` | `[tool.poe.tasks]` defining `check`, `fix`, and per-gate sub-tasks |
| `lockfile` | `uv.lock` pinning exact tool versions for reproducibility |

**Validation rules**
- Local and CI MUST read this same configuration and agree on verdict (FR-006/SC-005).
- The enabled rule set MUST be explicit/enumerated, not implicit defaults (FR-007).
- Changes MUST be diffable in `pyproject.toml` review (FR-010).

---

## Entity: Suppression

An auditable, justified silencing of one finding.

| Field | Description |
|-------|-------------|
| `scope` | A single finding on a single line — never file-wide or global |
| `mechanism` | `# noqa: <rule>` (ruff), `# pylint: disable=<check>` (+reason), `# nosec <id>` (bandit), ty inline ignore |
| `reason` | Required human justification adjacent to the suppression |
| `guard` | ruff `RUF100` flags unused/blanket `noqa`; review rejects unexplained disables |

**Validation rules**
- A suppression MUST reduce coverage for exactly the one finding, nothing else (FR-009/SC-007).
- A suppression without a recorded reason MUST be rejected in review.

---

## Relationships

```text
Gate Configuration (pyproject.toml)
        │ defines
        ▼
   Quality Gate ──produces──► Finding ──may be silenced by──► Suppression
   (5 instances)                                   (one finding scope)
```

No state machine is required; each gate run is stateless and idempotent — same inputs and
configuration yield the same findings and verdict.
