---

description: "Task list for Subphase Heading implementation"
---

# Tasks: Subphase Heading

**Input**: Design documents from `/specs/014-subphase-block/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/subphase-block.md, quickstart.md

**Tests**: Test tasks ARE included — the spec defines validation scenarios and the constitution's
Testing Standards are non-negotiable.

**Organization**: Grouped by user story so each is an independently testable increment.

> **Leanest feature in this series**: Per plan.md (and identically to `007-spanning-headline`), the
> entire implementation is a single-file change to `templates/cheatsheet.html.j2` (one dispatch
> branch, one custom property, one CSS rule). No Python code is touched. Every user story below is
> therefore test-only, verifying a distinct slice of the same mechanism.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1, US2

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: The `subphase` block dispatch.

- [X] T001 Add a `subphase` branch to the `render_block` macro's `{% if/elif %}` dispatch chain in `templates/cheatsheet.html.j2`, rendering `<h2 class="phase phase--sub">{{ block.title }}</h2>` (data-model.md; contracts/subphase-block.md)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The CSS that makes the new block actually render brighter.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 Add the `--green-subphase` custom property to the `:root` block in `templates/cheatsheet.html.j2`, with its light-mode (`#256b46`) and print-friendly grayscale (`#3d3d3d`) values, following the existing `--green-dark`/`--green-sub` pattern (data-model.md; research.md §2–3)
- [X] T003 Add the CSS rule `h2.phase--sub { background: var(--green-subphase); }` to the `<style>` block in `templates/cheatsheet.html.j2`, near the existing `.phase`/`.phase--spanning` rules (research.md §1)
- [X] T004 [P] Update the header doc comment in `templates/cheatsheet.html.j2` to document the new `subphase` block type alongside `phase`, `spanning_headline`, `page_break`, and `column_reset`

**Checkpoint**: `subphase` blocks now render with a brighter background; ready for story-level verification.

---

## Phase 3: User Story 1 - Insert a heading one level below a phase (Priority: P1) 🎯 MVP

**Goal**: A `subphase` block renders at the same width/position as `phase`, with a visibly brighter
background, and remains distinguishable from `phase` in print-friendly mode.

**Independent Test**: A fixture with a `phase` heading followed by a `subphase` heading shows the
`subphase` heading's rendered background luminance higher than the `phase` heading's, at equal width.

### Tests for User Story 1 ⚠️

- [X] T005 [US1] Integration test: a `subphase` heading's rendered background is brighter than a `phase` heading's, at the same width, in `tests/integration/test_subphase_pdf.py` (FR-002/FR-003; SC-001/SC-002)
- [X] T006 [P] [US1] Integration test: multiple `subphase` headings each render correctly and independently, and one at the very start and, separately, the very last block in the document (including without a preceding `phase`) renders without errors or unexpected blank space, in `tests/integration/test_subphase_pdf.py` (FR-005/FR-006; SC-003)
- [X] T007 [P] [US1] Integration test: content immediately before and after a `subphase` heading renders completely and in correct reading order, and a document combining `subphase` with `page_break`/`column_reset` produces the correct effect for each with no interference, in `tests/integration/test_subphase_pdf.py` (FR-009)
- [X] T008 [P] [US1] Extend `tests/integration/test_print_friendly_pdf.py`'s all-variants fixture with a `subphase` block, and add a test asserting `phase`/`subphase` resolve to two distinct grayscale shades in print-friendly mode (FR-004; SC-004)

### Implementation for User Story 1

- No story-specific implementation — Setup + Foundational (T001–T004) already deliver this behavior; T005–T008 verify it against the P1 acceptance criteria.

**Checkpoint**: MVP — a `subphase` heading reliably renders brighter than `phase`, at the same width, and stays distinguishable in print-friendly mode.

---

## Phase 4: User Story 2 - Subphase headings behave consistently across every language and edition (Priority: P2)

**Goal**: Equivalent `subphase` placement renders with the identical background color across every
language of a shared edition/revision.

**Independent Test**: An equivalent `subphase` heading in two languages' fixture content both render
with the identical background color at the equivalent content point.

### Tests for User Story 2 ⚠️

- [X] T009 [US2] Integration test: an equivalent `subphase` placement in two languages' fixture content renders with the identical background color at the equivalent point in both generated outputs, in `tests/integration/test_subphase_cross_language.py` (FR-007; SC-005)

### Implementation for User Story 2

- No story-specific implementation — `render_block` operates purely on already-resolved per-language content, so it is inherently language-agnostic; T009 verifies this holds in practice.

**Checkpoint**: Both stories independently functional — `subphase` headings render correctly, distinguishably, and consistently across languages.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation and documentation.

- [X] T010 Run every scenario in `quickstart.md` end-to-end (regression check against real `11e` content, brighter-background rendering, multiple headings, start/end placement, coexistence with `page_break`/`column_reset`, print-friendly distinguishability, cross-language) and confirm expected outcomes
- [X] T011 [P] Document `subphase` in `docs/CONTENT_AUTHORING.md` — authoring syntax, one example — with a link to `specs/014-subphase-block/contracts/subphase-block.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories. Contains the entire
  mechanism (T001–T004).
- **User Stories (Phase 3–4)**: All depend on Foundational and consist of test tasks verifying
  different acceptance-criteria slices of the same mechanism.
- **Polish (Phase 5)**: Depends on the desired stories being complete.

### User Story Dependencies

- **US1 (P1)**: Independent once Foundational is done.
- **US2 (P2)**: Independent once Foundational is done.

### Parallel Opportunities

- **Foundational**: T004 (doc comment) is independent of T002/T003, though all touch the same file
  (different regions).
- **US1**: T006, T007, T008 are all parallel to T005 (distinct independent cases; T008 in a
  different file).
- **Polish**: T011 parallel to T010.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001).
2. Complete Phase 2: Foundational (T002–T004) — CRITICAL; this is the entire mechanism.
3. Complete Phase 3: User Story 1 (T005–T008).
4. **STOP and VALIDATE**: a `subphase` fixture reliably renders brighter than `phase`, at the same
   width, and stays distinguishable in print-friendly mode.
5. Demonstrable MVP — a genuinely distinct, nested heading level.

### Incremental Delivery

1. Setup + Foundational → the mechanism exists.
2. US1 → brighter-background rendering + print-friendly distinguishability verified (MVP!) → validate → demo.
3. US2 → cross-language consistency verified → validate → demo.
4. Polish → quickstart validation (incl. real `11e` content regression check) + docs.

---

## Notes

- [P] = different files, no dependencies. Tasks sharing a file are grouped but remain logically
  independent.
- [Story] label maps each task to its user story for traceability.
- Because this feature's entire implementation lives in Setup + Foundational, each story's
  "Implementation" subsection intentionally contains no new tasks — only its Tests subsection does.
- Commit after each task or logical group; stop at any checkpoint to validate a story independently.
