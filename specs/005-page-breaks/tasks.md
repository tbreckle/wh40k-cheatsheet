---

description: "Task list for Page Breaks in Generated Output implementation"
---

# Tasks: Page Breaks in Generated Output

**Input**: Design documents from `/specs/005-page-breaks/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/page-break-block.md, quickstart.md

**Tests**: Test tasks ARE included — the spec defines validation scenarios and the constitution's
Testing Standards are non-negotiable.

**Organization**: Grouped by user story so each is an independently testable increment.

> **Lean change surface**: Per research.md, the entire mechanism (segmentation function, macro
> extraction, segment loop, CSS rule) is built once in Foundational. Each user story phase below adds
> **targeted test coverage** proving that shared mechanism satisfies its specific acceptance
> criteria — there is little/no story-specific *implementation* left after Foundational, which is
> expected for a feature this lean (two files changed total).

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1, US2, US3

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: The pure segmentation function every story's behavior depends on.

- [X] T001 Implement `group_by_page_breaks(blocks: list[dict]) -> list[list[dict]]` and register it as a Jinja2 template global in `_environment()` in `src/wh40k_cheatsheet/render/html_renderer.py`: split `blocks` into runs at each `{"type": "page_break"}` entry (marker consumed, not included in either run), discard runs with zero blocks (data-model.md; research.md §3/§5) — required a scoped `# ty: ignore[invalid-assignment]` suppression for an upstream Jinja2 stub imprecision on `env.globals`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Wire segmentation into the template so `page_break` blocks take effect. No new
dependencies; no new modules.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 Extract the existing per-block `{% if/elif %}` dispatch chain in `templates/cheatsheet.html.j2` (phase, subsection, paragraph, list, callout, table, keyvals, glossary, stratagem branches) into a `{% macro render_block(block) %}...{% endmacro %}`, with behavior for every existing block type unchanged (research.md §6) — also fixed a latent bug found during extraction: the fallback branch called an already-removed `rich()` macro, replaced with the same convention used by `paragraph`
- [X] T003 Replace the single `<div class="sheet">{% for block in document.blocks %}...{% endfor %}</div>` wrapper in `templates/cheatsheet.html.j2` with `{% for segment in group_by_page_breaks(document.blocks) %}<div class="sheet">{% for block in segment %}{{ render_block(block) }}{% endfor %}</div>{% endfor %}` (depends on T001, T002; contracts/page-break-block.md)
- [X] T004 Add the CSS rule `.sheet + .sheet { break-before: page; }` to the `<style>` block in `templates/cheatsheet.html.j2`, immediately after the existing `.sheet { column-count: 2; ... }` rule (research.md §2; verified empirically)

**Checkpoint**: `page_break` blocks now take effect; documents with zero markers render identically to before this feature (regression-safe, per plan.md Constraints).

---

## Phase 3: User Story 1 - Force a new page at a specific point in the content (Priority: P1) 🎯 MVP

**Goal**: One `page_break` marker produces exactly one extra page transition, with content after it
starting on the new page and content before it unaffected.

**Independent Test**: A fixture with one marker mid-document produces one more page than the same
content without it; content after the marker begins on that new page.

### Tests for User Story 1 ⚠️

- [X] T005 [US1] Unit test: `group_by_page_breaks()` with one marker mid-list produces exactly two non-empty segments split at that point, in `tests/unit/test_page_breaks.py` (FR-001/FR-002/FR-003)
- [X] T006 [P] [US1] Integration test: generating a fixture with one `page_break` marker produces exactly one more page than the same content without it, with content after the marker on the new page, in `tests/integration/test_page_break_pdf.py` (SC-001) — also added a dedicated segment-content-attribution assertion

### Implementation for User Story 1

- No story-specific implementation — the Foundational mechanism (T001–T004) already delivers this behavior; T005/T006 verify it against the P1 acceptance criteria.

**Checkpoint**: MVP — a single page-break marker works exactly as specified.

---

## Phase 4: User Story 2 - Use multiple page breaks in one document (Priority: P2)

**Goal**: Any number of markers each produce their own transition; consecutive markers with no
content between them collapse to a single transition; start/end markers never produce a blank page.

**Independent Test**: A fixture with three markers among four sections produces four pages; a
fixture with two consecutive markers produces one transition, not two blank pages.

### Tests for User Story 2 ⚠️

- [X] T007 [US2] Unit test: `group_by_page_breaks()` edge cases — marker at start, marker at end, and two consecutive markers all produce no empty segments, in `tests/unit/test_page_breaks.py` (FR-004/FR-005/FR-006; SC-002/SC-003)
- [X] T008 [P] [US2] Unit test: `group_by_page_breaks()` with three markers among four blocks produces four independent non-empty segments, in `tests/unit/test_page_breaks.py` (FR-007)
- [X] T009 [P] [US2] Integration test: a fixture with two consecutive `page_break` markers generates exactly one page transition at that point, not an extra blank page, in `tests/integration/test_page_break_pdf.py` (SC-003)

### Implementation for User Story 2

- No story-specific implementation — the Foundational "drop empty segments" rule (T001) already covers every edge case here; T007–T009 verify it.

**Checkpoint**: US1 and US2 both work — single and multiple/consecutive markers all behave correctly.

---

## Phase 5: User Story 3 - Page breaks behave consistently across every language and edition (Priority: P3)

**Goal**: Equivalent marker placement in different languages of the same edition/revision produces
equivalent pagination in each generated PDF.

**Independent Test**: Place an equivalent marker in both `en` and `de` `content.yaml` for the same
edition/revision; both generated PDFs show the same relative page-count increase.

### Tests for User Story 3 ⚠️

- [X] T010 [US3] Integration test: an equivalent `page_break` placement in two languages' `content.yaml` for the same edition/revision produces the same relative page-count increase in both generated PDFs, in `tests/integration/test_page_break_cross_language.py` (FR-008; SC-004)

### Implementation for User Story 3

- No story-specific implementation — `group_by_page_breaks()` operates purely on the already-resolved per-language `document.blocks`, so it is inherently language-agnostic; T010 verifies this holds in practice.

**Checkpoint**: All three stories independently functional — page breaks are correct, robust to edge cases, and consistent across languages.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation and documentation.

- [X] T011 Run every scenario in `quickstart.md` end-to-end (no-marker regression against real `11e` content, one marker, start/end markers, consecutive markers, multiple independent markers, cross-language consistency, page-footer counters) and confirm expected outcomes — real `11e` content still renders 3/3 pages (en/de, unchanged); footer `Page X / Y` confirmed correct via `pdftotext`; all marker scenarios covered by the automated test suite (15/15 passing)
- [X] T012 [P] Document the `page_break` block type in `README.md` (authoring syntax, one example) with a link to `specs/005-page-breaks/contracts/page-break-block.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories. Contains the entire
  implementation; T001–T004 are the whole feature.
- **User Stories (Phase 3–5)**: All depend on Foundational and consist of test tasks verifying
  different acceptance-criteria slices of the same mechanism — they may run in any order relative to
  each other.
- **Polish (Phase 6)**: Depends on the desired stories being complete.

### User Story Dependencies

- **US1 (P1)**: Independent once Foundational is done.
- **US2 (P2)**: Independent once Foundational is done (not sequentially dependent on US1, though both
  exercise the same `group_by_page_breaks()`).
- **US3 (P3)**: Independent once Foundational is done.

### Within Each User Story

- Tests only — there is no implementation step to sequence tests before, since Foundational already
  delivered the mechanism (T005 before nothing; T007/T008 before nothing; T010 before nothing).

### Parallel Opportunities

- **Foundational**: T002 and T004 touch the same file (`cheatsheet.html.j2`) but different regions
  (dispatch logic vs. CSS) — sequenced as T002 → T003 → T004 to keep the diff easy to review, though
  T004 could technically run in parallel with T002/T003.
- **US1**: T006 parallel to T005 (different files: integration test vs. unit test).
- **US2**: T008/T009 parallel to each other and to T007 (T007/T008 share a unit test file but cover
  distinct cases — group as one PR-sized edit; T009 is a different file, fully parallel).
- **US3**: T010 has no parallel counterpart within its story.
- **Polish**: T012 parallel to T011.

---

## Parallel Example: User Story 2 tests

```bash
# T009 (different file) is independent of T007/T008 (same unit test file):
Task: "Unit tests for edge cases + multi-marker segmentation in tests/unit/test_page_breaks.py"
Task: "Integration test for consecutive-marker collapse in tests/integration/test_page_break_pdf.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001).
2. Complete Phase 2: Foundational (T002–T004) — CRITICAL; this is the entire feature.
3. Complete Phase 3: User Story 1 (T005–T006).
4. **STOP and VALIDATE**: a one-marker fixture produces exactly one extra page transition.
5. Demonstrable MVP — deliberate, single page-break control.

### Incremental Delivery

1. Setup + Foundational → the mechanism exists and is regression-safe.
2. US1 → single-marker behavior verified (MVP!) → validate → demo.
3. US2 → multi-marker and edge-case behavior verified → validate → demo.
4. US3 → cross-language consistency verified → validate → demo.
5. Polish → quickstart validation (incl. real `11e` content regression check) + docs.

---

## Notes

- [P] = different files, no dependencies.
- [Story] label maps each task to its user story for traceability.
- Because this feature's entire implementation lives in Foundational, each story's "Implementation"
  subsection intentionally contains no new tasks — only its Tests subsection does. This is
  appropriate for a feature this lean; do not manufacture busywork implementation tasks where the
  Foundational phase already delivered the behavior.
- Tests (T005, T006, T007/T008, T009, T010) must fail before Foundational (T001–T004) is complete,
  and pass once it is.
- Commit after each task or logical group; stop at any checkpoint to validate a story independently.
