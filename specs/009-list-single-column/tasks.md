---

description: "Task list for List Single-Column (Full-Width) Flag implementation"
---

# Tasks: List Single-Column (Full-Width) Flag

**Input**: Design documents from `/specs/009-list-single-column/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/list-single-column-flag.md, quickstart.md

**Tests**: Test tasks ARE included — the spec defines validation scenarios and the constitution's
Testing Standards are non-negotiable.

**Organization**: Grouped by user story so each is an independently testable increment.

> **Leanest feature in this series**: Per plan.md, the entire implementation is a single-file
> change to `templates/cheatsheet.html.j2` (one conditional class + one CSS rule). No Python code is
> touched — `column-span: all` is orthogonal to `005-page-breaks`/`006-column-reset`'s segmentation,
> confirmed in research.md §3 (reusing `007-spanning-headline`'s already-proven conclusion). The
> single user story below is therefore test-only, verifying the same two-line mechanism from a
> different angle each time.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: The `list` block's conditional full-width dispatch.

- [X] T001 Add a conditional `block--full-width` class to the `list` branch's wrapper `<div class="block">` in the `render_block` macro in `templates/cheatsheet.html.j2`: `<div class="block{{ ' block--full-width' if block.single_column | default(false) else '' }}">` — `| default(false)` guard for `StrictUndefined`, matching the glossary `spanning` flag's exact pattern (data-model.md; contracts/list-single-column-flag.md)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The CSS that makes the flagged list actually span both columns.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 Add the CSS rule `.block--full-width { column-span: all; }` to the `<style>` block in `templates/cheatsheet.html.j2`, near the existing `.block`/`.phase--spanning` rules (research.md §1; verified empirically against the real template)
- [X] T003 [P] Update the header doc comment in `templates/cheatsheet.html.j2` to document the new `single_column` field on the `list` block type

**Checkpoint**: A `list` block with `single_column: true` now renders full-width; ready for story-level verification.

---

## Phase 3: User Story 1 - Give a specific list the full page width instead of a narrow column (Priority: P1) 🎯 MVP

**Goal**: A `list` block with `single_column: true` renders its items across the complete
two-column width, visually distinct from a standard, column-confined list.

**Independent Test**: A fixture with one flagged list and one standard list shows the flagged
list's rendered box width approximating the full content width, not a single column's width.

### Tests for User Story 1 ⚠️

- [X] T004 [US1] Integration test: a flagged list's rendered box width approximates the full content width, versus a standard list's single-column width, using the box-inspection methodology from research.md §1, in `tests/integration/test_list_single_column_pdf.py` (FR-001; SC-001) — verified via direct comparison of rendered `<ul>` block widths (flagged > 1.5× standard)
- [X] T005 [P] [US1] Integration test: content immediately before and after a flagged list renders completely and in correct reading order — before-content fills its column normally, after-content resumes fresh below the full-width list, in `tests/integration/test_list_single_column_pdf.py` (FR-003; SC-002)
- [X] T006 [P] [US1] Integration test: a flagged list whose items include nested `sub` entries renders those sub-items with normal indentation/bullet styling, fully readable at full width, in `tests/integration/test_list_single_column_pdf.py` (FR-003; data-model.md validation rules)
- [X] T007 [P] [US1] Integration test: a document combining a flagged list with `page_break` and `column_reset` at different points produces the correct effect for each, with no interference between the three features, in `tests/integration/test_list_single_column_pdf.py` (FR-004)
- [X] T008 [P] [US1] Integration test: a flagged list at the very start and, separately, the very last block in the document renders without errors or unexpected blank space, in `tests/integration/test_list_single_column_pdf.py` (Edge Cases)

### Implementation for User Story 1

- No story-specific implementation — Setup + Foundational (T001–T003) already deliver this behavior; T004–T008 verify it against the P1 acceptance criteria.

**Checkpoint**: MVP — a flagged list reliably renders full-width and distinguishably, with surrounding content, nested sub-items, and coexistence with other markers all correct.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation and documentation.

- [X] T009 Run every scenario in `quickstart.md` end-to-end (regression check against real `11e` content, full-width rendering, surrounding-content integrity, nested sub-items, coexistence with `page_break`/`column_reset`, start/end placement) and confirm expected outcomes
- [X] T010 [P] Document the `single_column` flag in `README.md` — authoring syntax, one example — with a link to `specs/009-list-single-column/contracts/list-single-column-flag.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS the user story. Contains the entire
  mechanism (T001–T003).
- **User Story 1 (Phase 3)**: Depends on Foundational and consists of test tasks verifying
  different acceptance-criteria slices of the same mechanism.
- **Polish (Phase 4)**: Depends on the story being complete.

### User Story Dependencies

- **US1 (P1)**: Independent once Foundational is done — the only user story in this feature.

### Within the User Story

- Tests only — there is no implementation step to sequence tests before, since Setup + Foundational
  already delivered the mechanism.

### Parallel Opportunities

- **Foundational**: T003 (doc comment) is independent of T002 (CSS rule), though both touch the same
  file (different regions).
- **US1**: T005, T006, T007, T008 are all parallel to each other and to T004 (same file, distinct
  independent cases).
- **Polish**: T010 parallel to T009.

---

## Parallel Example: User Story 1 tests

```bash
# Different, independent test cases within the same file:
Task: "Full-width box-width test in tests/integration/test_list_single_column_pdf.py"
Task: "Surrounding-content integrity test in tests/integration/test_list_single_column_pdf.py"
Task: "Nested sub-item rendering test in tests/integration/test_list_single_column_pdf.py"
Task: "Coexistence with page_break/column_reset test in tests/integration/test_list_single_column_pdf.py"
Task: "Start/end placement test in tests/integration/test_list_single_column_pdf.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001).
2. Complete Phase 2: Foundational (T002–T003) — CRITICAL; this is the entire mechanism.
3. Complete Phase 3: User Story 1 (T004–T008).
4. **STOP and VALIDATE**: a flagged list fixture reliably renders full-width and distinguishably.
5. Demonstrable MVP — deliberate full-width visual separation for lists that need it.

### Incremental Delivery

1. Setup + Foundational → the mechanism exists.
2. US1 → full-width rendering, surrounding-content integrity, nested sub-items, and coexistence
   with `005`/`006` all verified (MVP!) → validate → demo.
3. Polish → quickstart validation (incl. real `11e` content regression check) + docs.

---

## Notes

- [P] = different files, no dependencies. Tasks sharing a file are grouped but remain logically
  independent.
- [Story] label maps each task to its user story for traceability.
- Because this feature's entire implementation lives in Setup + Foundational, the story's
  "Implementation" subsection intentionally contains no new tasks — only its Tests subsection does.
- Tests (T004–T008) must fail before Foundational (T001–T003) is complete, and pass once it is.
- Commit after each task or logical group; stop at any checkpoint to validate independently.
