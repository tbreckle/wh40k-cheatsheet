---

description: "Task list for Column Reset in Generated Output implementation"
---

# Tasks: Column Reset in Generated Output

**Input**: Design documents from `/specs/006-column-reset/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/column-reset-block.md, quickstart.md

**Tests**: Test tasks ARE included — the spec defines validation scenarios and the constitution's
Testing Standards are non-negotiable.

**Organization**: Grouped by user story so each is an independently testable increment.

> **Evolves existing code**: This feature renames/evolves `005-page-breaks`'s
> `group_by_page_breaks()` into `group_by_breaks()` (new return shape: `list[Segment]` instead of
> `list[list[dict]]`). Foundational includes updating `005`'s existing tests to the new API —
> this is required, not optional, since the old function signature goes away.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1, US2, US3

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: The evolved, type-aware segmentation function every story's behavior depends on.

- [X] T001 Evolve `group_by_page_breaks(blocks)` into `group_by_breaks(blocks: list[dict]) -> list[Segment]` in `src/wh40k_cheatsheet/render/html_renderer.py`: define `Segment` (a frozen dataclass with `blocks: list[dict]` and `break_type: Literal["page", "soft"] | None`); single linear pass splitting on both `"page_break"` and `"column_reset"` markers, dropping empty segments (unchanged from 005), with an accumulating `pending` break-type that `page_break` always sets to `"page"` and `column_reset` sets to `"soft"` only if not already `"page"` (data-model.md algorithm; research.md §3–4); register `group_by_breaks` as the Jinja2 template global, replacing the old registration — **bug found and fixed during T011's testing**: the initial implementation never reset `pending` to `None` after closing a segment, so a `page_break`'s effect incorrectly leaked forward across a later, unrelated `column_reset` (e.g. `[a, page_break, b, column_reset, c]` incorrectly gave `c` `break_type="page"` instead of `"soft"`); fixed by resetting `pending = None` immediately after closing each segment, before applying the next marker's own contribution

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Wire the evolved function into the template and CSS; keep `005`'s existing behavior
regression-safe under the new API.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 Update `templates/cheatsheet.html.j2`: change `{% for segment in group_by_page_breaks(document.blocks) %}` to `{% for segment in group_by_breaks(document.blocks) %}`; render `<div class="sheet sheet--soft">` when `segment.break_type == "soft"` else `<div class="sheet">`; iterate `segment.blocks` (was `segment` directly) inside (depends on T001; contracts/column-reset-block.md)
- [X] T003 Add the CSS rule `.sheet + .sheet.sheet--soft { break-before: auto; }` to `templates/cheatsheet.html.j2`, immediately after the existing `.sheet + .sheet { break-before: page; }` rule (research.md §1; verified empirically)
- [X] T004 [P] Update the header doc comment in `templates/cheatsheet.html.j2` to document the new `column_reset` block type alongside `page_break`
- [X] T005 Update `tests/unit/test_page_breaks.py` and `tests/integration/test_page_break_pdf.py` (from `005-page-breaks`) to call `group_by_breaks()` and assert against `Segment.blocks`/`Segment.break_type` instead of the old `list[list[dict]]` shape, without changing what behavior they verify — CRITICAL regression guard for `005` — **adapted**: only `test_page_breaks.py` needed changes (it calls the renamed function directly, asserting on the new `Segment` shape); `test_page_break_pdf.py` exercises the template end-to-end via `render_html()` and needed no changes, since `break_type in {"page", None}` renders the identical `<div class="sheet">` string as before

**Checkpoint**: `005`'s `page_break` behavior is fully regression-safe under the renamed/evolved API; `column_reset` blocks now resolve to `break_type == "soft"` segments, ready for story-level verification.

> **Detour during Foundational verification**: the mandatory regression check against real `11e`
> content initially appeared to show `page_break` had stopped isolating "USING STRATAGEMS" onto its
> own page. Extensive investigation (8 independent CSS-level mitigation attempts, a full
> `pypdf`-based document-splitting architecture prototype) turned out to be chasing a **non-bug**:
> the `page_break` marker had been relocated by an earlier, unrelated content edit to sit before the
> stratagem cards rather than before "USING STRATAGEMS" — `page_break` was working correctly the
> whole time, just for a different boundary than remembered. The `pypdf` prototype and its
> dependency were fully reverted; no trace of it remains in the shipped code. This is recorded here
> so a future reader doesn't rediscover the same dead end.

---

## Phase 3: User Story 1 - Force the next content to start fresh in the left column (Priority: P1) 🎯 MVP

**Goal**: A `column_reset` marker produces a `"soft"` segment whose content begins in a left column,
regardless of where the preceding content ended.

**Independent Test**: A fixture with a `column_reset` after content that reached the right column
produces a segment whose content starts at the top of a left column.

### Tests for User Story 1 ⚠️

- [X] T006 [US1] Unit test: `group_by_breaks()` — a `column_reset` marker produces a `break_type == "soft"` segment; edge cases (marker at start, marker at end, consecutive markers) produce no empty segments, in `tests/unit/test_column_reset.py` (FR-001/FR-002/FR-005/FR-006/FR-007)
- [X] T007 [P] [US1] Integration test: content after a `column_reset` lands in a left column, verified via rendered-layout box-position inspection (per research.md §2 methodology), in `tests/integration/test_column_reset_pdf.py` (SC-001) — also covers the "regardless of preceding column" acceptance scenario

### Implementation for User Story 1

- No story-specific implementation — the Foundational mechanism (T001–T004) already delivers this behavior; T006/T007 verify it against the P1 acceptance criteria.

**Checkpoint**: MVP — a `column_reset` marker reliably realigns content to the left column.

---

## Phase 4: User Story 2 - Reset without wasting a whole page (Priority: P2)

**Goal**: A `column_reset` stays on the same page when room remains, and only spills to the next page
through natural overflow when it doesn't — never an unconditional forced page like `page_break`.

**Independent Test**: A fixture with ample room remaining keeps the reset content on the same page; a
fixture with a genuinely full page lets the reset content overflow naturally.

### Tests for User Story 2 ⚠️

- [X] T008 [US2] Integration test: a `column_reset` with room remaining on the current page produces the same page count as the same content without the marker (no page wasted), in `tests/integration/test_column_reset_pdf.py` (SC-002)
- [X] T009 [P] [US2] Integration test: a `column_reset` placed after enough content to fill a page causes the following content to overflow naturally onto the next page, still landing in that page's left column, in `tests/integration/test_column_reset_pdf.py` (SC-002)

### Implementation for User Story 2

- No story-specific implementation — the `break-before: auto` override (T003) already delivers this; T008/T009 verify it.

**Checkpoint**: US1 and US2 both work — resets realign to the left column and never waste a page unnecessarily.

---

## Phase 5: User Story 3 - Combine column resets with page breaks predictably (Priority: P3)

**Goal**: `column_reset` and `page_break` (`005`) coexist correctly; when adjacent with nothing
between them, `page_break` always wins, regardless of order.

**Independent Test**: A fixture with `page_break` and `column_reset` adjacent, in both orders,
produces a full page break in both cases; a fixture using both markers independently at different
points produces the correct effect at each point.

### Tests for User Story 3 ⚠️

- [X] T010 [US3] Unit test: `group_by_breaks()` priority-merge rule — `page_break` immediately adjacent to `column_reset`, in both orders, resolves the following segment to `break_type == "page"`, in `tests/unit/test_column_reset.py` (FR-009)
- [X] T011 [P] [US3] Integration test: a document using `page_break` and `column_reset` independently at different, non-adjacent points produces the correct effect at each — pages forced only where `page_break` occurs, left-column realignment (with or without a page, as appropriate) at each `column_reset`, in `tests/integration/test_column_reset_pdf.py` (SC-004) — **this test caught the real `pending`-reset bug fixed in T001**
- [X] T012 [P] [US3] Integration test: an equivalent `column_reset` placement across two languages' fixture content produces the equivalent same-page-or-overflow outcome in both, in `tests/integration/test_column_reset_cross_language.py` (FR-010/SC-005) — **adapted file path**: kept separate from `test_column_reset_pdf.py` to mirror `005`'s `test_page_break_cross_language.py` convention

### Implementation for User Story 3

- No story-specific implementation — the priority-merge accumulator in `group_by_breaks()` (T001) already delivers this; T010–T012 verify it.

**Checkpoint**: All three stories independently functional — resets work, don't waste pages, and combine correctly with page breaks.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation and documentation.

- [X] T013 Run every scenario in `quickstart.md` end-to-end (regression check against real `11e` content; same-page reset; overflow reset; start/end/consecutive; mixed-marker adjacency both orders; independent combined use; cross-language) and confirm expected outcomes — real `11e` content verified at **3 pages** both languages (not 4 — see the Foundational detour note: the existing `page_break` marker sits before the stratagem cards, not before "USING STRATAGEMS"; per user direction, exact page count doesn't matter, only that the mechanisms work correctly, which they do); footer counters confirmed correct via `pdftotext`
- [X] T014 [P] Document `column_reset` in `README.md` — authoring syntax, one example, and a short note on how it differs from `page_break` — with a link to `specs/006-column-reset/contracts/column-reset-block.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories. Contains the entire
  mechanism (T001–T003) plus the mandatory regression update to `005`'s tests (T005).
- **User Stories (Phase 3–5)**: All depend on Foundational and consist of test tasks verifying
  different acceptance-criteria slices of the same mechanism.
- **Polish (Phase 6)**: Depends on the desired stories being complete.

### User Story Dependencies

- **US1 (P1)**: Independent once Foundational is done.
- **US2 (P2)**: Independent once Foundational is done.
- **US3 (P3)**: Independent once Foundational is done; specifically exercises the priority-merge
  accumulator that US1/US2 don't need to touch.

### Within Each User Story

- Tests only — there is no implementation step to sequence tests before, since Foundational already
  delivered the mechanism.

### Parallel Opportunities

- **Foundational**: T004 (doc comment) is independent of T002/T003 (same file, different regions) —
  sequenced together for review clarity, but could run in parallel. T005 (test regression update) is
  a different file, parallel to T002–T004.
- **US1**: T007 parallel to T006 (different files).
- **US2**: T009 parallel to T008 (share a file but distinct, independent cases — group as one PR-sized
  edit or split; listed [P] since they don't depend on each other's code).
- **US3**: T011/T012 parallel to T010 and each other (T010 is a different file from T011/T012).
- **Polish**: T014 parallel to T013.

---

## Parallel Example: User Story 3 tests

```bash
# T010 (unit, different file) is independent of T011/T012 (integration, same file, distinct cases):
Task: "Unit test priority-merge rule in tests/unit/test_column_reset.py"
Task: "Integration test independent combined use + cross-language in tests/integration/test_column_reset_pdf.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001).
2. Complete Phase 2: Foundational (T002–T005) — CRITICAL; this is the entire mechanism plus the
   mandatory `005` regression update.
3. Complete Phase 3: User Story 1 (T006–T007).
4. **STOP and VALIDATE**: a `column_reset` fixture reliably realigns content to the left column.
5. Demonstrable MVP — deliberate column realignment.

### Incremental Delivery

1. Setup + Foundational → the mechanism exists, `005` regression-safe.
2. US1 → left-column realignment verified (MVP!) → validate → demo.
3. US2 → same-page-if-room / natural-overflow behavior verified → validate → demo.
4. US3 → priority-merge and cross-language consistency verified → validate → demo.
5. Polish → quickstart validation (incl. real `11e` content regression check) + docs.

---

## Notes

- [P] = different files, no dependencies.
- [Story] label maps each task to its user story for traceability.
- Because this feature's entire implementation lives in Foundational (mirroring `005-page-breaks`'s
  structure), each story's "Implementation" subsection intentionally contains no new tasks — only
  its Tests subsection does.
- T005 is not optional busywork — `group_by_page_breaks()`'s signature change means `005`'s existing
  tests will fail to even import/call correctly without it.
- Tests (T006, T007, T008/T009, T010, T011/T012) must fail before Foundational (T001–T004) is
  complete, and pass once it is.
- Commit after each task or logical group; stop at any checkpoint to validate a story independently.
