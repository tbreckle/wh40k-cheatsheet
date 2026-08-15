# Implementation Plan: Google-Style Docstrings Everywhere

**Branch**: `008-google-style-docstrings` | **Date**: 2026-08-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/008-google-style-docstrings/spec.md`

## Summary

Every module, class, function, and method in `src/wh40k_cheatsheet` — public and private alike —
gets a Google-style docstring (`tests/` stays exempt, per FR-006), and the project's existing
quality-gate stack (ruff + pylint, from `001-python-quality-gates`) is extended to enforce both
*presence* and *accuracy* (documented params/returns/raises actually match the signature)
automatically, the same way it already enforces formatting/lint/type correctness. Research
(research.md) empirically verified the exact tool configuration needed: ruff's `D` (pydocstyle)
rules only ever check *public* symbols by design, so pylint (with its `no-docstring-rgx` override)
is the sole presence-enforcer across the full public+private scope, while ruff's `D` rules are kept
for their Google-style *formatting* checks; pylint's bundled `docparams` extension (no new
dependency) enforces accuracy once its permissive `accept-no-*-doc` defaults are turned off. No new
third-party tool is introduced, consistent with the spec's Assumptions.

## Technical Context

**Language/Version**: Python 3.12+ (shared with features 001–007)

**Primary Dependencies**: None new. ruff (existing dev dependency) gains the `D` rule family;
pylint (existing dev dependency) gains its own bundled `pylint.extensions.docparams` plugin, which
ships with pylint itself.

**Storage**: N/A — this is a code-documentation and quality-gate-configuration feature.

**Testing**: pytest. A config-assertion unit test verifies the `pyproject.toml` settings
(ruff `D` selection + `pydocstyle.convention`, pylint's `no-docstring-rgx`/`load-plugins`/
`accept-no-*-doc` values) are actually what research.md specifies. A subprocess-based gate
self-test — mirroring the pattern `001-python-quality-gates` originally designed (a seeded "bad"
fixture that must fail the gate, and a clean fixture that must pass) — proves the *mechanism* really
catches a missing docstring and a mismatched-signature docstring, not just that config keys exist.

**Target Platform**: Same as features 001–007 — local dev + CI (Linux).

**Project Type**: Single project. This feature changes `pyproject.toml`'s quality-gate configuration
and adds docstrings to the existing 16 `.py` files under `src/wh40k_cheatsheet`; it introduces no new
source modules and changes no runtime behavior.

**Performance Goals**: N/A — docstrings and lint config do not touch any runtime code path; no
impact on the existing PDF-generation performance budgets.

**Constraints**: Must not alter any runtime behavior — every source-file change is additive
(docstring text only). Must not introduce false-positive lint noise beyond genuine missing/malformed
docstrings — research.md confirms type-annotated parameters don't need redundant type prose, and the
`google` pydocstyle convention avoids conflicting formatting rules.

**Scale/Scope**: `pyproject.toml` config changes across four sections (`ruff.lint`,
`ruff.lint.pydocstyle`, `ruff.lint.per-file-ignores`, and four `pylint.*` sections) plus docstrings
added across all 16 existing files in `src/wh40k_cheatsheet`. research.md's empirical measurement:
55 currently-undocumented public symbols (ruff `D`) / 65 total including private symbols (pylint) —
this is the concrete retrofit scope for User Story 3.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment |
|-----------|------------|
| I. Code Quality | **Directly satisfied.** This feature *is* an extension of the tooling-enforced quality bar the principle mandates — docstring correctness becomes another gate-enforced dimension alongside lint/format/types. |
| II. Testing Standards (NON-NEGOTIABLE) | **Satisfied by design.** A gate self-test proves the mechanism catches a missing docstring and a signature/docstring mismatch, not merely that config keys are set — mirroring `001`'s own seeded-fixture pattern. |
| III. User Experience Consistency | **N/A to end-user UX** (no user-facing surface — this feature touches only `src/` documentation and quality-gate config). The "user" here is the contributor; consistent Google-style formatting everywhere serves the same predictability goal this principle asks for. |
| IV. Performance Requirements | **N/A.** Docstrings and lint rules add no runtime code; `poe check`'s local-run time increases negligibly (existing ruff/pylint invocations already parse every file's AST). |
| Additional Constraints & Standards | **Satisfied.** No new dependency; config stays centralized in the single `pyproject.toml`, version-controlled and human-reviewable. |
| Development Workflow & Quality Gates | **Directly satisfied.** Ships through the same PR-gated `poe check` workflow as every prior feature; a docstring violation now blocks merge exactly like an existing lint/type/security violation. |

**Verdict**: PASS. No violations; Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/008-google-style-docstrings/
├── plan.md               # This file
├── research.md            # Phase 0 output (empirical ruff/pylint verification)
├── data-model.md          # Phase 1 output
├── quickstart.md          # Phase 1 output
├── contracts/
│   └── docstring-style.md   # The Google-style docstring contract + gate configuration contract
└── tasks.md                 # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root) — changes to existing files

```text
pyproject.toml
    # CHANGED:
    #  - [tool.ruff.lint] select gains "D"
    #  - [tool.ruff.lint.pydocstyle] convention = "google"  (new section)
    #  - [tool.ruff.lint.per-file-ignores] "tests/**" gains "D"
    #  - [tool.pylint."messages control"] disable list loses missing-module-docstring /
    #    missing-class-docstring / missing-function-docstring (re-enabled)
    #  - [tool.pylint.main] load-plugins gains "pylint.extensions.docparams"  (new key)
    #  - [tool.pylint.basic] no-docstring-rgx = "^$"  (new section; overrides default "^_")
    #  - [tool.pylint.parameter_documentation] accept-no-param-doc/accept-no-return-doc/
    #    accept-no-raise-doc/accept-no-yields-doc = false, default-docstring-type = "google"
    #    (new section)

src/wh40k_cheatsheet/**/*.py
    # CHANGED (all 16 existing files): every module gains a module-level docstring; every
    # public and private class/function/method gains a Google-style docstring (summary,
    # Args:, Returns:, Raises: as applicable) — content-only changes, no logic touched.
    #  - Includes the two explicit dunder methods in revision/identifier.py
    #    (RevisionId.__str__, RevisionId.__lt__), which are not exempt (research.md §3).

tests/
├── unit/test_docstring_gate_config.py         # NEW: pyproject.toml settings match research.md
├── unit/fixtures/bad_docstring_example.py      # NEW: seeded violations (missing + mismatched)
├── unit/fixtures/good_docstring_example.py     # NEW: fully compliant fixture
└── integration/test_docstring_gate_selftest.py # NEW: subprocess ruff/pylint against both
                                                   # fixtures above — bad fails with the
                                                   # expected codes, good passes clean
```

**Structure Decision**: No new source modules — this is a configuration change to the single
`pyproject.toml` plus additive docstring content across the existing package. Test additions follow
`001-python-quality-gates`'s originally-designed (there, deferred) gate self-test pattern: seeded
fixture files plus a subprocess-based test proving the gate actually catches what it's configured to
catch.

## Complexity Tracking

> No constitution violations. Section intentionally left empty.
