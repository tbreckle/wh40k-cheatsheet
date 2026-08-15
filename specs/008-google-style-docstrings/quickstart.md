# Quickstart: Google-Style Docstrings Everywhere

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md) ·
Contract: [contracts/docstring-style.md](./contracts/docstring-style.md)

Validates docstring presence, formatting, and accuracy enforcement end-to-end on top of the
existing `001-python-quality-gates` stack. Assumes the implementation tasks have updated
`pyproject.toml` per the gate configuration contract and added docstrings across `src/`.

## Prerequisites

Same as feature 001: `uv sync`.

## Validation scenarios

### Scenario 1 — The full repository passes clean (US1/US3, SC-001/SC-004)

```bash
uv run poe check
```

**Expected**: `poe lint` (ruff `D` rules + pylint's docstring/`docparams` checks) reports zero
docstring-related findings anywhere in `src/wh40k_cheatsheet` — the retrofit is complete and the
whole suite (format/lint/security/types/tests) stays green.

### Scenario 2 — pydoc/help() shows a real, useful docstring (US1, SC-002)

```bash
uv run python -c "from wh40k_cheatsheet.pipeline import generate; help(generate)"
uv run python -m pydoc wh40k_cheatsheet.pipeline
```

**Expected**: `help(generate)` shows a one-line summary, an `Args:` section for every parameter, and
a `Returns:` section — readable without opening `pipeline.py`. The module-level `pydoc` output shows
the module's own summary docstring plus every class/function's docstring, Google-style formatted.

### Scenario 3 — Missing docstring fails the gate (US2, SC-003)

```bash
cat >> src/wh40k_cheatsheet/pipeline.py << 'EOF'

def _scratch_undocumented(x: int) -> int:
    return x * 2
EOF
uv run poe lint
git checkout -- src/wh40k_cheatsheet/pipeline.py
```

**Expected**: `poe lint` fails, reporting `missing-function-docstring` (pylint) and `D103` (ruff) at
the exact line the scratch function was added — a private-*looking* addition still gets caught since
it isn't actually underscore-prefixed here; repeat with a leading underscore in the name to confirm
private symbols are caught identically. Revert afterward (shown above) — this is a throwaway check,
not a real change.

### Scenario 4 — Mismatched Args/Returns fails the gate (US2, SC-003)

Temporarily add a function with a Google-style docstring that omits a real parameter, or claims a
`Returns:` section on a function that returns `None`, and re-run `poe lint`.

**Expected**: pylint reports `missing-param-doc`/`differing-param-doc`/`missing-return-doc` as
appropriate, at the exact symbol — the gate catches inaccurate documentation, not just its absence.

### Scenario 5 — `tests/` stays exempt (FR-006)

```bash
uv run ruff check --select D tests
```

**Expected**: zero findings — `tests/` was never in scope, confirmed directly.

## Success signals

- `poe check` is green with zero docstring-related findings against the current `src/` tree
  (SC-001/SC-004).
- Any public function's purpose, parameters, and return value are readable via `pydoc`/`help()`
  alone (SC-002).
- A deliberately undocumented or inaccurately-documented change is automatically rejected by the
  existing gate workflow, no manual review needed to catch it (SC-003).
