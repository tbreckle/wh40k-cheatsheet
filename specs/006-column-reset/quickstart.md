# Quickstart: Column Reset in Generated Output

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md) ·
Contract: [contracts/column-reset-block.md](./contracts/column-reset-block.md)

Validates `column_reset` markers end-to-end on top of the existing `002`/`005` generator. Assumes
the implementation tasks have added the `column_reset` block type, evolved `group_by_breaks()`, the
template's conditional `sheet--soft` class, and the `.sheet + .sheet.sheet--soft` CSS rule.

## Prerequisites

Same as features 002–005: `uv sync`, WeasyPrint native libraries installed, `project.yaml` present.

## Validation scenarios

### Scenario 1 — Regression: `005`'s `page_break` behavior is unchanged

```bash
uv run wh40k-cheatsheet generate --edition 11e --language en
pdfinfo out/11e/2026-08-01-00/en.pdf | grep Pages
```

**Expected**: page count matches the current baseline (4 pages — the real `11e` content already has
one `page_break` before "USING STRATAGEMS"). `column_reset` is not yet used in real content, so this
proves the evolved `group_by_breaks()` produces identical output for existing `page_break`-only
content.

### Scenario 2 — Reset stays on the same page when room remains (US1/US2, SC-001/SC-002)

Author a fixture with a `column_reset` placed after a short section.

**Expected**: the section after the marker begins in a left column, and the PDF has the same page
count as the same content without the marker (no page was wasted).

### Scenario 3 — Reset overflows naturally when the page is full (US2, SC-002)

Author a fixture with enough content before a `column_reset` to fill a page.

**Expected**: the content after the marker lands on the next page, still starting in that page's left
column — the reset did not disappear or misplace content, it simply followed normal overflow.

### Scenario 4 — Start/end/consecutive markers produce no unexpected blank space (Edge Cases, SC-003)

Author fixtures with `column_reset` as the very first block, the very last block, and twice in a row.

**Expected**: none of these produce blank pages or blank column regions, matching `005`'s equivalent
guarantees for `page_break`.

### Scenario 5 — Mixed markers: `page_break` always wins when adjacent (US3, SC-004)

Author a fixture with `page_break` and `column_reset` adjacent (no content between them), in both
orders.

**Expected**: both orderings force a full page break for the following content — confirming the
priority-merge rule is order-independent.

### Scenario 6 — Both marker types used independently in one document (US3, SC-004)

Author a fixture using several `page_break` and `column_reset` markers at different, non-adjacent
points.

**Expected**: each marker produces its own correct, independent effect — `page_break` points always
start new pages; `column_reset` points always start a left column, forcing a new page only when
necessary.

### Scenario 7 — Consistent across languages (US1, SC-005)

Place an equivalent `column_reset` in both `en` and `de` fixture content for the same
edition/revision; generate both.

**Expected**: both PDFs show the marker taking effect at the equivalent content point, with the same
same-page-or-overflow outcome.

## Success signals

- Existing `page_break`-only content (the real `11e` cheat sheet) is completely unaffected (SC-004
  regression safety, inherited from `005`).
- A `column_reset` with room remaining never costs a page (SC-002).
- A `column_reset` always lands its following content in a left column, whether same-page or after
  overflow (SC-001).
- Adjacent mixed markers always resolve to a full page break, regardless of order (SC-004).
- Leading/trailing/consecutive markers of either type never produce blank space (SC-003).
