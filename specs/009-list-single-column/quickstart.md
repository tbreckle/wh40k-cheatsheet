# Quickstart: List Single-Column (Full-Width) Flag

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md) ·
Contract: [contracts/list-single-column-flag.md](./contracts/list-single-column-flag.md)

Validates the `list` block's `single_column` flag end-to-end on top of the existing
`002`/`005`/`006`/`007` generator. Assumes the implementation task has added the conditional class
in the `list` branch and the `.block--full-width` CSS rule.

## Prerequisites

Same as features 002–008: `uv sync`, WeasyPrint native libraries installed, `project.yaml` present.

## Validation scenarios

### Scenario 1 — Regression: existing content unaffected

```bash
uv run wh40k-cheatsheet generate --edition 11e
```

**Expected**: real `11e` content (which doesn't set `single_column` on any `list` block) renders
identically to before this feature — same page count, same layout.

### Scenario 2 — Flagged list renders full-width (US1, SC-001)

Author a fixture with a `list` block that has `single_column: true`, alongside a standard list
without the flag.

**Expected**: the flagged list's rendered box width approximates the full page content width, while
the standard list's width approximates a single column's width (per research.md §1's box-inspection
methodology).

### Scenario 3 — Surrounding content stays correctly placed (SC-002)

Author distinct, identifiable content immediately before and after a flagged list.

**Expected**: both render completely, in correct reading order — content before fills its column
normally; content after resumes in fresh two-column flow beneath the full-width list.

### Scenario 4 — Nested sub-items render correctly at full width

Author a flagged list whose items include nested `sub` entries.

**Expected**: sub-items render with their normal indentation/bullet styling, fully readable at the
full page width.

### Scenario 5 — Coexists with page_break and column_reset (FR-004)

Author a fixture combining a flagged list with a `page_break` and a `column_reset` at different
points.

**Expected**: each feature behaves exactly as documented in its own contract, with no interference
between them.

### Scenario 6 — Start/end placement (Edge Cases)

Author fixtures with a flagged list as the very first and, separately, the very last block.

**Expected**: both render correctly with no errors or unexpected blank space.

## Success signals

- A flagged list's background/text always covers the complete two-column width (SC-001).
- Surrounding content is never cut off, duplicated, or misplaced (SC-002).
- Existing content without the flag renders byte-identically to before this feature (SC-003).
- No code changes were needed to add/move/remove the flag — only content edits (SC-004).
