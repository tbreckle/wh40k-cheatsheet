# Contract: Quality Command Interface

Feature: [spec.md](../spec.md) · Plan: [plan.md](../plan.md)

The quality gates expose a **command contract** — the interface contributors and CI depend on. It is
defined as poethepoet tasks in `[tool.poe.tasks]` and invoked through uv. This contract is what
downstream tasks and CI must honor; the exact rule contents are configuration detail.

---

## Commands

| Command | Purpose | Exit code contract |
|---------|---------|--------------------|
| `uv run poe check` | Run ALL gates (format-check, lint, security, types, tests) and report every finding | `0` iff every gate passes; non-zero if any gate fails |
| `uv run poe fix` | Apply auto-fixable formatting and lint corrections | `0` after applying fixes; does not gate |
| `uv run poe lint` | ruff check + pylint only | `0` iff lint passes |
| `uv run poe format-check` | ruff format --check only | `0` iff already formatted |
| `uv run poe security` | bandit only | `0` iff no findings at/above configured severity |
| `uv run poe types` | ty only | `0` iff type check passes |
| `uv run poe test` | pytest only | `0` iff all tests pass |

`poe check` is the single canonical entrypoint (FR-001). CI runs exactly `uv run poe check`
(FR-006).

---

## Behavioral contract

1. **Aggregate & non-zero on any failure** (FR-002): `poe check` returns non-zero if *any* gate
   reports a violation, `0` only when *all* pass.
2. **Independent gates** (FR-004): each gate runs even if an earlier gate failed; findings from all
   gates are surfaced in one run, not short-circuited at the first failure.
3. **Attributed findings** (FR-003): every reported finding names its gate, file, and line.
4. **Fail loud on missing tool** (FR-011): if a gate's tool cannot execute, `poe check` reports that
   explicitly and returns non-zero — it MUST NOT report success by skipping.
5. **Local == CI** (FR-006/SC-005): the same command and the same `pyproject.toml` configuration
   produce the same pass/fail verdict in both environments.
6. **Python floor** (FR-008): all gates evaluate against Python 3.12+ semantics.

---

## Gate self-test contract (makes SC-003 executable)

A pytest-based test asserts the gate suite catches each category using
`tests/fixtures/bad_example.py`, a file that deliberately contains:

| Seeded defect | Gate expected to catch it | Example rule |
|---------------|---------------------------|--------------|
| Style/format violation | `format` / `lint` (ruff) | `E`/format diff |
| Likely bug pattern | `lint` (ruff bugbear / pylint) | `B006` mutable default arg |
| Hard-coded secret | `security` (bandit) | `B105`/`S105` |
| Type error | `types` (ty) | assign `str` to `int` |

**Contract**: running the gates against the fixture yields at least one finding in each of the four
categories, and running them against a clean file yields none. The fixture is excluded from the
normal `src/` gate targets so it does not fail the real build.

---

## CI contract

`.github/workflows/quality.yml`:

- **Trigger**: pull requests targeting `main` (and pushes to `main`).
- **Steps**: checkout → install uv → `uv sync` (locked) → `uv run poe check`.
- **Enforcement**: the job is a required status check; a failing `poe check` blocks merge
  (FR-005/SC-002).
- **Parity**: no CI-only flags that change verdicts vs. local (SC-005).
