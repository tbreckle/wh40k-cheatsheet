---

description: "Task list for Full-Width Spanning Headline implementation"
---

# Tasks: Full-Width Spanning Headline

**Input**: Design documents from `/specs/007-spanning-headline/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/spanning-headline-block.md, contracts/glossary-spanning-flag.md, quickstart.md

**Tests**: Test tasks ARE included — the spec defines validation scenarios and the constitution's
Testing Standards are non-negotiable.

**Organization**: Grouped by user story so each is an independently testable increment.

> **Leanest feature in this series**: Per plan.md, the entire implementation is a single-file
> change to `templates/cheatsheet.html.j2` (one dispatch branch + one CSS rule). No Python code is
> touched — `column-span: all` is orthogonal to `005-page-breaks`/`006-column-reset`'s segmentation,
> confirmed in research.md §2. Every user story below is therefore test-only, verifying a distinct
> slice of the same two-line mechanism. The 2026-08-14 Phase 7 addition (glossary `spanning` flag)
> is the one exception — it's a one-line conditional-class change reusing the same CSS rule, so it
> carries its own single implementation task (T011) ahead of its tests.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1, US2, US3

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: The `spanning_headline` block dispatch.

- [X] T001 Add a `spanning_headline` branch to the `render_block` macro's `{% if/elif %}` dispatch chain in `templates/cheatsheet.html.j2`, rendering `<h2 class="phase phase--spanning">{{ block.title }}</h2>` (data-model.md; contracts/spanning-headline-block.md)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The CSS that makes the new block actually span both columns.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 Add the CSS rule `.phase--spanning { column-span: all; }` to the `<style>` block in `templates/cheatsheet.html.j2`, near the existing `.phase`/`.sheet` rules (research.md §1; verified empirically)
- [X] T003 [P] Update the header doc comment in `templates/cheatsheet.html.j2` to document the new `spanning_headline` block type alongside `phase`, `page_break`, and `column_reset`

**Checkpoint**: `spanning_headline` blocks now render as full-width bands; ready for story-level verification.

---

## Phase 3: User Story 1 - Insert a headline that visually spans both columns (Priority: P1) 🎯 MVP

**Goal**: A `spanning_headline` block renders its text and background across the complete two-column
width, visually distinct from the standard single-column heading.

**Independent Test**: A fixture with one `spanning_headline` between two sections shows that
headline's rendered box width approximating the full content width, not a single column's width.

### Tests for User Story 1 ⚠️

- [X] T004 [US1] Integration test: a `spanning_headline`'s rendered box width approximates the full content width, versus a standard `phase` heading's single-column width, using the box-inspection methodology from research.md §1, in `tests/integration/test_spanning_headline_pdf.py` (FR-001/FR-002/FR-003; SC-001/SC-004) — verified via direct comparison of rendered `<h2>` block widths (spanning > 1.5× standard)
- [X] T005 [P] [US1] Integration test: multiple `spanning_headline` blocks each render correctly and independently, and one at the very start and, separately, the very last block in the document renders without errors or unexpected blank space, in `tests/integration/test_spanning_headline_pdf.py` (FR-006/FR-007; SC-003)

### Implementation for User Story 1

- No story-specific implementation — Setup + Foundational (T001–T003) already deliver this behavior; T004/T005 verify it against the P1 acceptance criteria.

**Checkpoint**: MVP — a spanning headline reliably renders full-width and distinguishably.

---

## Phase 4: User Story 2 - Content on either side of the spanning headline stays correctly placed (Priority: P2)

**Goal**: Content immediately before and after a `spanning_headline` renders completely and in
correct order, and the feature coexists correctly with `page_break`/`column_reset`.

**Independent Test**: Distinct, identifiable content before and after a spanning headline both
render completely, in expected reading order.

### Tests for User Story 2 ⚠️

- [X] T006 [US2] Integration test: content immediately before and after a `spanning_headline` renders completely and in correct reading order — before-content fills its column normally, after-content resumes fresh below the span, in `tests/integration/test_spanning_headline_pdf.py` (FR-004/FR-005; SC-002)
- [X] T007 [P] [US2] Integration test: a document combining `spanning_headline` with `page_break` and `column_reset` at different points produces the correct effect for each, with no interference between the three features, in `tests/integration/test_spanning_headline_pdf.py` (FR-010)

### Implementation for User Story 2

- No story-specific implementation — the orthogonal architecture (research.md §2) already guarantees this; T006/T007 verify it.

**Checkpoint**: US1 and US2 both work — spanning headlines render correctly and never corrupt surrounding content or interfere with existing pagination features.

---

## Phase 5: User Story 3 - Spanning headlines behave consistently across every language and edition (Priority: P3)

**Goal**: Equivalent `spanning_headline` placement renders equivalently across every language of a
shared edition/revision.

**Independent Test**: An equivalent `spanning_headline` in two languages' fixture content both
render full-width at the equivalent content point.

### Tests for User Story 3 ⚠️

- [X] T008 [US3] Integration test: an equivalent `spanning_headline` placement in two languages' fixture content renders full-width at the equivalent point in both generated outputs, in `tests/integration/test_spanning_headline_cross_language.py` (FR-008; SC-005)

### Implementation for User Story 3

- No story-specific implementation — `render_block` operates purely on already-resolved per-language content, so it is inherently language-agnostic; T008 verifies this holds in practice.

**Checkpoint**: All three stories independently functional — spanning headlines render correctly, preserve surrounding content, and are consistent across languages.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation and documentation.

- [X] T009 Run every scenario in `quickstart.md` end-to-end (regression check against real `11e` content, full-width rendering, surrounding-content integrity, multiple headlines, start/end placement, coexistence with `page_break`/`column_reset`, cross-language) and confirm expected outcomes — real `11e` content confirmed unaffected (3 pages, both languages, unchanged); all other scenarios covered by the automated test suite (8/8 new tests passing)
- [X] T010 [P] Document `spanning_headline` in `README.md` — authoring syntax, one example — with a link to `specs/007-spanning-headline/contracts/spanning-headline-block.md`

---

## Phase 7: Addition (2026-08-14) - Glossary Spanning Flag

**Purpose**: Extend the existing `glossary` block (`002-pdf-generation`) with an optional `spanning`
flag that reuses the `phase--spanning` mechanism from Phase 2 for the glossary's title bar only, per
the 2026-08-14 clarification session (spec.md FR-011/SC-007).

**Goal**: `glossary` blocks with `spanning: true` render their title full-width, identically to a
standalone `spanning_headline`; the term list is unaffected; existing content without the flag is
byte-for-byte unchanged.

**Independent Test**: A fixture `glossary` block with `spanning: true` shows its title's rendered box
width approximating the full content width (same methodology as T004), while its term-list markup is
identical to the same block with the flag omitted.

- [X] T011 [US1] Add a conditional `phase--spanning` class to the glossary title in the `render_block` macro's `glossary` branch in `templates/cheatsheet.html.j2`: `<h2 class="phase{{ ' phase--spanning' if block.spanning | default(false) else '' }}">{{ block.title | default('Core Abilities') }}</h2>` — reuses the CSS rule from T002 verbatim, no new CSS (data-model.md; contracts/glossary-spanning-flag.md) — `| default(false)` guard added to satisfy `StrictUndefined` when the optional key is absent
- [X] T012 [P] [US1] Integration test: a `glossary` block with `spanning: true` renders its title box width approximating the full content width (same box-inspection methodology as T004), while its `<div class="glossary">` term-list markup is byte-identical to the same block rendered without the flag, in `tests/integration/test_glossary_spanning_pdf.py` (FR-011; SC-007)
- [X] T013 [P] [US1] Integration test: a `glossary` block with `spanning` omitted (or falsy) renders identically to a `glossary` block from before this addition — explicit regression coverage for the default-off behavior, in `tests/integration/test_glossary_spanning_pdf.py` (data-model.md validation rules)
- [X] T014 [P] Document the glossary `spanning` flag in `README.md` — one example — with a link to `specs/007-spanning-headline/contracts/glossary-spanning-flag.md`

**Checkpoint**: The glossary spanning flag works, defaults to off with zero behavior change for
existing content (including the real `11e` glossary block), and reuses the already-verified CSS
mechanism with no new empirical risk.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories. Contains the entire
  mechanism (T001–T003).
- **User Stories (Phase 3–5)**: All depend on Foundational and consist of test tasks verifying
  different acceptance-criteria slices of the same mechanism.
- **Polish (Phase 6)**: Depends on the desired stories being complete.
- **Addition (Phase 7)**: Depends on Foundational (reuses its CSS rule directly); independent of
  Phases 3–6, though thematically an extension of User Story 1.

### User Story Dependencies

- **US1 (P1)**: Independent once Foundational is done.
- **US2 (P2)**: Independent once Foundational is done.
- **US3 (P3)**: Independent once Foundational is done.

### Within Each User Story

- Tests only — there is no implementation step to sequence tests before, since Setup + Foundational
  already delivered the mechanism.

### Parallel Opportunities

- **Foundational**: T003 (doc comment) is independent of T002 (CSS rule), though both touch the same
  file (different regions).
- **US1**: T005 parallel to T004 (same file, distinct independent cases).
- **US2**: T007 parallel to T006 (same file, distinct independent cases).
- **Polish**: T010 parallel to T009.
- **Addition (Phase 7)**: T012, T013, and T014 are all parallel once T011 lands — T012/T013 are
  distinct independent test cases in the same new test file, and T014 (README) touches a different
  file entirely.

---

## Parallel Example: User Story 2 tests

```bash
# Different, independent test cases within the same file:
Task: "Surrounding-content integrity test in tests/integration/test_spanning_headline_pdf.py"
Task: "Coexistence with page_break/column_reset test in tests/integration/test_spanning_headline_pdf.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001).
2. Complete Phase 2: Foundational (T002–T003) — CRITICAL; this is the entire mechanism.
3. Complete Phase 3: User Story 1 (T004–T005).
4. **STOP and VALIDATE**: a spanning headline fixture reliably renders full-width and distinguishably.
5. Demonstrable MVP — deliberate full-width visual separation.

### Incremental Delivery

1. Setup + Foundational → the mechanism exists.
2. US1 → full-width rendering verified (MVP!) → validate → demo.
3. US2 → surrounding-content integrity and coexistence with `005`/`006` verified → validate → demo.
4. US3 → cross-language consistency verified → validate → demo.
5. Polish → quickstart validation (incl. real `11e` content regression check) + docs.

---

## Notes

- [P] = different files, no dependencies. Tasks sharing a file are grouped but remain logically
  independent.
- [Story] label maps each task to its user story for traceability.
- Because this feature's entire implementation lives in Setup + Foundational, each story's
  "Implementation" subsection intentionally contains no new tasks — only its Tests subsection does.
- Tests (T004/T005, T006/T007, T008) must fail before Foundational (T001–T003) is complete, and pass
  once it is.
- Commit after each task or logical group; stop at any checkpoint to validate a story independently.
- Phase 7 (T011–T014, added 2026-08-14) extends the existing `glossary` block with the `spanning`
  flag from `contracts/glossary-spanning-flag.md`. T012/T013 must fail before T011 lands and pass
  once it does; T013 specifically guards the default-off regression case (real `11e` glossary
  content unaffected).

---

## Phase 8: Bug Fix (2026-08-15) — Spanning Glossary Fragmenting Into 4 Columns

**Purpose**: Reported directly against real `11e` content: the CORE ABILITIES glossary (36 terms,
`spanning: true`) rendered as 4 narrow columns instead of 2. Root cause: Phase 7 applied spanning to
the glossary's `<h2>` title only, per the 2026-08-14 clarification; the `<div class="glossary">` term
list, left in normal (non-spanning) flow, is tall enough to fragment across the outer article's
2-column layout, and each fragment independently applies the div's own `column-count: 2` —> 4 visible
columns. See spec.md's 2026-08-15 amendment and `contracts/glossary-spanning-flag.md`.

- [X] T015 Add a `glossary--spanning` CSS class (`column-span: all;`) in `templates/cheatsheet.html.j2`, applied to the `<div class="glossary">` alongside the existing `phase--spanning` class on its `<h2>`, conditionally on `block.spanning`
- [X] T016 [P] Update `tests/integration/test_glossary_spanning_pdf.py`: add a regression test asserting the glossary term-list div itself (not just the title) spans full width when `spanning: true`; narrow the old byte-identical-markup test to compare term *content* only (the wrapping div's class now legitimately differs)
- [X] T017 [P] Update `contracts/glossary-spanning-flag.md`, `data-model.md`, `quickstart.md`, `plan.md`, `spec.md` (Clarifications amendment, edge case, FR-011, Key Entities, SC-007), and `README.md`'s glossary-spanning section for the corrected behavior
- [X] T018 Regenerate the real `11e` English and German PDFs and visually confirm CORE ABILITIES / KERNFÄHIGKEITEN render as 2 full-width columns, not 4

**Checkpoint**: `poe check` green; real `11e` content (both languages) shows the glossary as one
full-width, 2-column block.
