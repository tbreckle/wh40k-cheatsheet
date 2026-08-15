# Quickstart: Full-Width Spanning Headline

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md) ·
Contracts: [contracts/spanning-headline-block.md](./contracts/spanning-headline-block.md),
[contracts/glossary-spanning-flag.md](./contracts/glossary-spanning-flag.md)

Validates `spanning_headline` (and the glossary's `spanning` flag) end-to-end on top of the existing
`002`/`005`/`006` generator. Assumes the implementation task has added the `render_block` dispatch
branch and `.phase--spanning` CSS rule.

## Prerequisites

Same as features 002–006: `uv sync`, WeasyPrint native libraries installed, `project.yaml` present.

## Validation scenarios

### Scenario 1 — Regression: existing content unaffected

```bash
uv run wh40k-cheatsheet generate --edition 11e
```

**Expected**: real `11e` content (which doesn't use `spanning_headline`) renders identically to
before this feature — same page count, same layout.

### Scenario 2 — Spanning headline renders full-width (US1, SC-001)

Author a fixture with a `spanning_headline` between two sections.

**Expected**: the headline's background and text stretch across the complete two-column width;
inspecting the rendered box width shows it approximating the full content width, not a single
column's width (per research.md §1's box-inspection methodology).

### Scenario 3 — Surrounding content stays correctly placed (US2, SC-002)

Author distinct, identifiable content immediately before and after a spanning headline.

**Expected**: both sections render completely, in correct reading order — content before fills its
column normally; content after resumes in fresh two-column flow beneath the span.

### Scenario 4 — Multiple spanning headlines (Edge Cases, SC-003)

Author a fixture with two or more `spanning_headline` blocks at different points.

**Expected**: each renders independently and correctly as its own full-width band.

### Scenario 5 — Start/end placement (Edge Cases)

Author fixtures with `spanning_headline` as the very first and, separately, the very last block.

**Expected**: both render correctly with no errors or unexpected blank space.

### Scenario 6 — Coexists with page_break and column_reset (Edge Cases, FR-010)

Author a fixture combining a `spanning_headline` with a `page_break` and a `column_reset` at
different points.

**Expected**: each feature behaves exactly as documented in its own contract, with no interference
between them.

### Scenario 7 — Consistent across languages (US3, SC-005)

Place an equivalent `spanning_headline` in two languages' fixture content for the same
edition/revision; generate both.

**Expected**: both PDFs show the headline spanning full-width at the equivalent content point.

### Scenario 8 — Glossary spanning flag (2026-08-14 addition, amended 2026-08-15, FR-011/SC-007)

Author a fixture `glossary` block with `spanning: true`, and generate the real `11e` content, whose
CORE ABILITIES glossary block sets `spanning: true` with 36 real terms.

**Expected**: the glossary's title AND its term list both span both columns as one full-width,
2-column block — not the 4-narrow-column fragmentation bug that shipped 2026-08-14 and was fixed
2026-08-15. A glossary block that omits the flag renders identically to before this addition
(regression-safe default-off behavior).

## Success signals

- A spanning headline's background/text always covers the complete two-column width (SC-001).
- Surrounding content is never cut off, duplicated, or misplaced (SC-002).
- Multiple spanning headlines each render correctly and independently (SC-003).
- The spanning headline is visually distinguishable from the standard heading purely by its shape
  (SC-004).
- Equivalent placement renders equivalently across languages (SC-005).
- No code changes were needed to add/move/remove a spanning headline — only content edits (SC-006).
- The glossary's `spanning` flag defaults to off and never changes existing content's output;
  enabling it spans both the title and the term list as one full-width, 2-column block (SC-007).
