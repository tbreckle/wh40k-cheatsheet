# Implementation Plan: Edition Revisions

**Branch**: `003-edition-revisions` | **Date**: 2026-08-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-edition-revisions/spec.md`

## Summary

Add a **revision** level between edition and language in the WH40K cheatsheet generator. A revision
is a corrected version of an edition's content, identified by `YYYY-MM-DD-NN` (valid calendar date +
two-digit daily sequence `00`–`99`). Revisions are **discovered from the source directory layout**
(`editions/<edition-id>/<revision-id>/<lang-code>/`) rather than declared in `project.yaml`, keeping
the config structure-only (consistent with feature 002's FR-019). A new `revision` module parses,
validates, orders, and selects revisions; the `content` resolver, `pipeline`, and CLI from feature
002 gain a revision segment. Generation defaults to the **latest** revision of an edition and accepts
an explicit `--revision` override. Templates are unchanged by revisions (a correction fixes content,
not layout), so template resolution continues to come from the edition/language config.

## Technical Context

**Language/Version**: Python 3.12+ (shared with features 001/002)

**Primary Dependencies**: No new third-party dependencies. Reuses Pydantic (validation), and the
Jinja2/WeasyPrint/PyYAML pipeline from feature 002. Revision parsing uses the standard library
(`datetime.date` for calendar-date validation, `re` for the identifier grammar).

**Storage**: Filesystem. New layout segment: `editions/<edition-id>/<revision-id>/<lang-code>/`.
Revisions are discovered by listing directories under an edition.

**Testing**: pytest (from feature 001). Revision parsing/ordering/validation unit tests; latest-
selection and explicit-selection integration tests; malformed/absent-revision error tests.

**Target Platform**: Local dev + CI (Linux), same as feature 002.

**Project Type**: Single project — extends the `src/wh40k_cheatsheet/` package.

**Performance Goals**: Revision discovery + selection adds negligible overhead; overall generation
stays within feature 002's <10s per (edition, language) PDF budget.

**Constraints**: `project.yaml` remains structure-only (no revision lists) — revisions come from the
filesystem. Identifier ordering must be total and deterministic so "latest" is unambiguous (FR-005).
Selection is scoped per edition (FR-013).

**Scale/Scope**: Up to 100 revisions/day per edition (`NN` 00–99); realistically a handful of
revisions per edition over time. Discovery is a single directory listing per edition.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment |
|-----------|------------|
| I. Code Quality | **Satisfied.** A small, cohesive `revision` module behind a clear boundary; typed `RevisionId` value object; runs under the feature-001 gates. |
| II. Testing Standards (NON-NEGOTIABLE) | **Satisfied.** Identifier parsing/validation/ordering are pure and highly testable; latest/explicit selection and error paths get integration tests. |
| III. User Experience Consistency | **Served.** Predictable default (latest) with explicit override; clear, consistent errors for malformed/unknown/absent revisions (never silent). |
| IV. Performance Requirements | **Satisfied.** One directory listing + in-memory sort per edition; no measurable impact on the generation budget. |
| Additional Constraints & Standards | **Advanced.** Revisions make the constitution's source-traceability requirement precise — every output is attributable to a dated correction (FR-012). Config stays version-controlled and structure-only. |
| Development Workflow & Quality Gates | **Satisfied.** Ships under the same PR-gated workflow as 001/002. |

**Verdict**: PASS. No violations; Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/003-edition-revisions/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── revision-identifier.md   # YYYY-MM-DD-NN grammar + ordering + validation contract
│   └── revision-selection.md    # CLI generate/list behavior with revisions
└── tasks.md             # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root) — changes to the feature-002 package

```text
src/wh40k_cheatsheet/
├── revision/                # NEW
│   ├── __init__.py
│   ├── identifier.py        # RevisionId value object: parse/validate/order (YYYY-MM-DD-NN)
│   └── discovery.py         # Discover revisions under editions/<edition-id>/, pick latest
├── content/
│   └── resolver.py          # CHANGED: resolve editions/<edition>/<revision>/<lang>/
├── pipeline.py              # CHANGED: resolve revision (latest or requested) before content
└── cli.py                   # CHANGED: `generate --revision`, `list` shows revisions

editions/                    # CHANGED convention (adds a revision segment)
└── <edition-id>/
    └── <revision-id>/        # e.g. 2026-08-01-00
        └── <lang-code>/      # strings + HTML fragments (as in feature 002)

tests/
├── unit/test_revision_identifier.py   # NEW: parse/validate/order/edge cases
├── unit/test_revision_discovery.py    # NEW: discovery + latest selection + malformed handling
├── integration/test_generate_revision.py  # NEW: default-latest, explicit, unknown, none
└── fixtures/                          # CHANGED: fixture editions gain revision dirs
```

**Structure Decision**: Extend the feature-002 single-project package with one new `revision`
module (identifier value object + filesystem discovery) and thread a revision through the existing
`content` resolver, `pipeline`, and `cli`. Revisions live in the source layout, not in `project.yaml`,
preserving the structure-only config decision from feature 002 while making "latest" computable from
the filesystem.

## Complexity Tracking

> No constitution violations. Section intentionally left empty.
