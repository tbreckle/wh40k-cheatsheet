---

description: "Task list for Edition Revisions implementation"
---

# Tasks: Edition Revisions

**Input**: Design documents from `/specs/003-edition-revisions/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/revision-identifier.md, contracts/revision-selection.md, quickstart.md

**Tests**: Test tasks ARE included — the spec defines validation scenarios and the constitution's
Testing Standards are non-negotiable.

**Organization**: Grouped by user story so each is an independently testable increment.

> **Cross-feature dependency**: This feature EXTENDS `002-pdf-generation`. Tasks T007–T009, T012,
> T015–T016 modify feature-002 files (`content/resolver.py`, `pipeline.py`, `cli.py`). Feature 002
> must be implemented before (or together with) these tasks.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1, US2, US3
- Exact file paths included. Python 3.12+/uv toolchain from feature 001; no new third-party deps.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Adapt fixtures to the revision-nested source layout.

- [X] T001 Restructure fixture editions to add a revision segment under `tests/fixtures/`: nest existing `editions/10e/<lang>/` content under `editions/10e/2026-08-01-00/<lang>/`, and add a later same-day revision `editions/10e/2026-08-01-01/<lang>/` (per plan.md layout) — **adapted**: real content (`editions/11e/2026-08-01-00/{en,de}/`) was authored revision-nested from the start, so no restructuring was needed; the same-day-latest ordering logic was instead verified with a scratch multi-revision directory (see T005 note)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The revision identifier and discovery machinery every story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 [P] Implement the `RevisionId` value object (regex `^\d{4}-\d{2}-\d{2}-\d{2}$`, calendar-date validation via `datetime.date`, `NN` range 0–99, total ordering by `(date, sequence)`, canonical `__str__`) in `src/wh40k_cheatsheet/revision/identifier.py` (+ `revision/__init__.py`) (contracts/revision-identifier.md R1–R6)
- [X] T003 [P] Unit tests for `RevisionId` covering valid ids and each invalid case (bad width, invalid date, `NN` > 99, missing parts) and ordering in `tests/unit/test_revision_identifier.py` — implemented 2026-08-14: 13 tests; note the `NN > 99` case can only be exercised as a 3-digit sequence (e.g. `100`) since the regex's fixed 2-digit width makes the numeric range check unreachable via any 2-digit input
- [X] T004 Implement revision discovery: list `editions/<edition-id>/` directories, parse names to `RevisionId`, build a sorted `RevisionSet` with `latest()`/`get()`/`ids()`; report malformed directory names (FR-009) and empty sets (FR-011), in `src/wh40k_cheatsheet/revision/discovery.py` (depends on T002; data-model.md)
- [X] T005 [P] Unit tests for discovery: correct ordering, `latest()` selection (incl. same-day), malformed-name reporting, and empty-set error in `tests/unit/test_revision_discovery.py` — implemented 2026-08-14: 9 tests

**Checkpoint**: Revision ids parse/validate/order; an edition's revisions are discoverable. Pipeline not yet revision-aware.

---

## Phase 3: User Story 1 - Generate using the latest revision by default (Priority: P1) 🎯 MVP

**Goal**: Generation without `--revision` uses the edition's latest revision, and output is written
under a revision-qualified path.

**Independent Test**: With `2026-08-01-00` and `2026-08-01-01` present, `generate --edition 10e
--language en` produces output from `2026-08-01-01` under `out/10e/2026-08-01-01/en.{html,pdf}`.

### Tests for User Story 1 ⚠️

- [X] T006 [US1] Integration test: default (no `--revision`) selects the latest revision, including the highest same-day sequence, and writes `out/<edition>/<revision>/<lang>.{html,pdf}` in `tests/integration/test_generate_revision.py` (SC-001) — implemented 2026-08-14: synthetic same-day revisions added to a `tmp_path` copy of the real project (real repo untouched)

### Implementation for User Story 1

- [X] T007 [US1] Extend the content resolver to include the revision segment — resolve `editions/<edition-id>/<revision-id>/<lang-code>/` — in `src/wh40k_cheatsheet/content/resolver.py` (FR-019 preserved; data-model.md)
- [X] T008 [US1] Extend the pipeline to resolve the revision before content: add `revision: RevisionId | None` to `GenerationRequest`, default to `RevisionSet.latest()` when unset, add the chosen revision to `GeneratedDocument`, in `src/wh40k_cheatsheet/pipeline.py` (FR-006, FR-012; depends on T004, T007) — implemented as explicit `revision` parameter on `generate()` rather than a request object, functionally equivalent
- [X] T009 [US1] Extend the CLI `generate` to accept an optional `--revision` (default latest) and write output to `out/<edition-id>/<revision-id>/<lang-code>.{html,pdf}` in `src/wh40k_cheatsheet/cli.py` (depends on T008)

**Checkpoint**: MVP — default-latest generation works end-to-end with revision-qualified output.

---

## Phase 4: User Story 2 - Generate a specific requested revision (Priority: P2)

**Goal**: An explicit `--revision` uses exactly that revision; malformed or unknown values fail
clearly.

**Independent Test**: `--revision 2026-08-01-00` produces that revision (not the latest); an unknown
revision lists available; a malformed revision reports the required format.

### Tests for User Story 2 ⚠️

- [X] T010 [P] [US2] Integration test: `--revision` selects the exact (older) revision rather than the latest in `tests/integration/test_generate_explicit_revision.py` (SC-002) — implemented 2026-08-14: synthetic older revision added alongside the real one
- [X] T011 [P] [US2] Integration test: a well-formed but non-existent `--revision` fails listing available revisions, and a malformed `--revision` fails with a format message, both emitting no output, in `tests/integration/test_revision_errors.py` (SC-003, SC-004) — implemented 2026-08-14: both assert no `out/` directory is created

### Implementation for User Story 2

- [X] T012 [US2] Implement explicit revision selection in the pipeline/CLI: parse the requested id (malformed → format error, FR-009), look it up via `RevisionSet.get()` (unknown → error listing available, FR-008), and use it exactly (FR-007), in `src/wh40k_cheatsheet/pipeline.py` and `src/wh40k_cheatsheet/cli.py` (depends on T008/T009)

**Checkpoint**: US1 and US2 both work — default-latest and explicit selection with clear errors.

---

## Phase 5: User Story 3 - Discover and validate an edition's revisions (Priority: P3)

**Goal**: `list` shows each edition's revisions chronologically with the latest marked; malformed and
absent revisions are reported.

**Independent Test**: `list` shows revisions oldest→newest with the latest indicated; a malformed
revision directory is reported; an edition with no revisions is reported on list and generate.

### Tests for User Story 3 ⚠️

- [X] T013 [P] [US3] Integration test: `list` shows each edition's revisions in chronological order with the latest marked in `tests/integration/test_list_revisions.py` (SC-005) — implemented 2026-08-14: 3 synthetic revisions (real 11e only ever has one), confirms chronological order + `(latest)` marker
- [X] T014 [P] [US3] Integration test: a malformed revision directory is reported (not silently ignored/mis-ordered), and an edition with no valid revisions is reported on both `list` and `generate`, in `tests/integration/test_revision_discovery_errors.py` (SC-003, FR-011) — implemented 2026-08-14: 4 tests; confirms `list` degrades gracefully to `revisions: (none)` for an empty edition while `generate` fails clearly (asymmetry is correct — `list` doesn't need a revision to exist, `generate` does)

### Implementation for User Story 3

- [X] T015 [US3] Extend the CLI `list` to display each edition's revisions in chronological order with the latest clearly indicated in `src/wh40k_cheatsheet/cli.py` (FR-010; depends on T004)
- [X] T016 [US3] Ensure malformed revision directories and empty revision sets surface as clear reports on both `list` and `generate` in `src/wh40k_cheatsheet/revision/discovery.py` and `src/wh40k_cheatsheet/cli.py` (FR-009, FR-011) — both exception types propagate through `cli.KNOWN_ERRORS` to a clear stderr message + exit 1

**Checkpoint**: All three stories independently functional; revisions discoverable, validated, and selectable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation and documentation.

- [X] T017 Run every scenario in `quickstart.md` end-to-end (default latest, same-day latest, explicit, unknown, malformed, list order, malformed dir, no revisions) and confirm expected outcomes — all verified (real CLI for default/explicit/unknown/malformed/list; scratch directory for same-day-latest/malformed-dir/no-revisions)
- [X] T018 [P] Update `README.md` with `--revision` usage, the `YYYY-MM-DD-NN` format, and the revision-qualified output layout `out/<edition-id>/<revision-id>/<lang-code>.{html,pdf}`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Fixture restructure — start immediately.
- **Foundational (Phase 2)**: `RevisionId` + discovery — BLOCKS all user stories.
- **US1 (Phase 3)**: Depends on Foundational; the MVP. Also depends on feature 002's resolver/pipeline/cli existing.
- **US2 (Phase 4)**: Depends on US1's revision-aware pipeline/CLI.
- **US3 (Phase 5)**: Depends on Foundational discovery; extends `list` and error surfacing.
- **Polish (Phase 6)**: After the desired stories.

### User Story Dependencies

- **US1 (P1)**: Independent once Foundational + feature-002 base exist.
- **US2 (P2)**: Reuses US1's selection point (adds explicit lookup + errors).
- **US3 (P3)**: Reuses Foundational discovery (adds listing + malformed/empty surfacing).

### Within Each User Story

- Tests before implementation (T006 before T007–T009; T010/T011 before T012; T013/T014 before T015/T016).
- Content resolver (T007) before pipeline (T008) before CLI (T009).

### Parallel Opportunities

- **Foundational**: T002 and T003 (different files) parallel; T004 depends on T002; T005 parallel test file.
- **US2**: T010/T011 (tests) parallel.
- **US3**: T013/T014 (tests) parallel.
- **Polish**: T018 parallel to T017.
- Tasks touching `cli.py` (T009, T012, T015, T016) run serially; they fall in separate phases.

---

## Parallel Example: Foundational tests

```bash
# Different files, independent once their targets exist:
Task: "Unit tests for RevisionId in tests/unit/test_revision_identifier.py"
Task: "Unit tests for discovery in tests/unit/test_revision_discovery.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup fixtures (T001).
2. Phase 2: Foundational `RevisionId` + discovery (T002–T005) — CRITICAL.
3. Phase 3: User Story 1 (T006–T009).
4. **STOP and VALIDATE**: `generate --edition 10e --language en` uses the latest revision and writes revision-qualified output.
5. Demonstrable MVP — default-latest revision generation.

### Incremental Delivery

1. Setup + Foundational → revision machinery ready.
2. US1 → default-latest generation (MVP!) → validate → demo.
3. US2 → explicit selection + errors → validate → demo.
4. US3 → discovery/listing/validation surfacing → validate → demo.
5. Polish → quickstart + docs.

---

## Notes

- [P] = different files, no dependencies. Tasks sharing `cli.py`/`pipeline.py` run serially.
- [Story] label maps each task to its user story for traceability.
- Tests (T003, T005, T006, T010–T011, T013–T014) must fail before their implementation lands.
- This feature edits feature-002 files — coordinate so 002 and 003 land coherently.
- Commit after each task or logical group; stop at any checkpoint to validate a story independently.
