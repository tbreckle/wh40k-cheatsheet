# Quickstart: Page Breaks in Generated Output

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md) ·
Contract: [contracts/page-break-block.md](./contracts/page-break-block.md)

Validates page-break markers end-to-end on top of the existing `002`/`003` generator. Assumes the
implementation tasks have added the `page_break` block type, `group_by_page_breaks()`, the template
segment loop, and the `.sheet + .sheet` CSS rule.

## Prerequisites

Same as features 002–004: `uv sync`, WeasyPrint native libraries installed, `project.yaml` present.

## Validation scenarios

### Scenario 1 — No markers: behavior unchanged (regression check)

```bash
uv run wh40k-cheatsheet generate --edition 11e --language en
pdfinfo out/11e/2026-08-01-00/en.pdf | grep Pages
```

**Expected**: page count matches the pre-feature baseline (3 pages) — content with zero `page_break`
markers is unaffected (plan.md Constraints).

### Scenario 2 — One marker forces exactly one extra page transition (US1, SC-001)

Add a temporary `content.yaml` fixture with one `page_break` between two phases; generate it.

**Expected**: the generated PDF has exactly one more page than the same content without the marker,
and the content after the marker begins on that new page.

### Scenario 3 — Marker at start / end produces no blank page (Edge Cases, SC-002)

Author fixtures with `page_break` as the very first and, separately, the very last block.

**Expected**: neither fixture produces a leading or trailing blank page — page count matches the
no-marker baseline for that content.

### Scenario 4 — Consecutive markers collapse (US2, SC-003)

Author a fixture with two `page_break` blocks back-to-back (nothing between them).

**Expected**: exactly one page transition occurs at that point — not two, not a blank page between
them.

### Scenario 5 — Multiple independent markers (US2, SC-001/SC-003)

Author a fixture with three `page_break` markers at different points among four sections.

**Expected**: four segments, four pages, each starting with its own section.

### Scenario 6 — Consistent across languages (US3, SC-004)

Place an equivalent `page_break` in both `en/content.yaml` and `de/content.yaml` for the same
edition/revision; generate both.

```bash
uv run wh40k-cheatsheet generate --edition 11e
pdfinfo out/11e/2026-08-01-00/en.pdf | grep Pages
pdfinfo out/11e/2026-08-01-00/de.pdf | grep Pages
```

**Expected**: both PDFs show the same relative page-count increase from their respective no-marker
baselines, and the break occurs at the equivalent content point in each.

### Scenario 7 — Page footer stays correct (contract G8)

Generate any content with 2+ markers and inspect the footer text.

**Expected**: `Page X / Y` in the footer correctly reflects the running page number and the true
total page count across all segments.

## Success signals

- Zero-marker documents render identically to before this feature (no regression).
- One marker → exactly one extra page transition, content correctly relocated (SC-001).
- Start/end markers never produce a blank page (SC-002).
- Consecutive markers never produce more than one transition (SC-003).
- Equivalent placement produces equivalent pagination across every language (SC-004).
- No code or tooling changes were needed to add/move/remove a marker — only content edits (SC-005).
