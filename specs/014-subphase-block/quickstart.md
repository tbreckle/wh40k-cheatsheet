# Quickstart: Subphase Heading

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md) ·
Contracts: [contracts/subphase-block.md](./contracts/subphase-block.md)

Validates `subphase` end-to-end on top of the existing generator. Assumes the implementation task has
added the `render_block` dispatch branch, the `--green-subphase` custom property, and the
`.phase--sub` CSS rule.

## Prerequisites

Same as prior features: `uv sync`, WeasyPrint native libraries installed, `project.yaml` present.

## Validation scenarios

### Scenario 1 — Regression: existing content unaffected

```bash
uv run wh40k-cheatsheet generate --edition 11e
```

**Expected**: real `11e` content (which doesn't use `subphase`) renders identically to before this
feature — same page count, same layout, same colors.

### Scenario 2 — Subphase renders brighter than phase (US1, SC-001/SC-002)

Author a fixture with a `phase` heading immediately followed by a `subphase` heading.

**Expected**: both render at the same width/position (single column); the `subphase` heading's
background is a visibly brighter shade of green than the `phase` heading's (inspected via rendered
box `background_color`).

### Scenario 3 — Multiple subphase headings (Edge Cases, SC-003)

Author a fixture with two or more `subphase` blocks at different points.

**Expected**: each renders independently and correctly with the same brighter background.

### Scenario 4 — Start/end placement (Edge Cases, FR-006)

Author fixtures with `subphase` as the very first and, separately, the very last block — including
without any preceding `phase`.

**Expected**: both render correctly with no errors or unexpected blank space.

### Scenario 5 — Coexists with page_break and column_reset (Edge Cases, FR-009)

Author a fixture combining `subphase` with a `page_break` and a `column_reset` at different points.

**Expected**: each feature behaves exactly as documented in its own contract, with no interference
between them.

### Scenario 6 — Distinguishable in print-friendly mode (Edge Cases, SC-004)

Generate the same fixture with `--print-friendly`.

**Expected**: `phase` and `subphase` resolve to two distinct, distinguishable grayscale shades —
never the same shade.

### Scenario 7 — Consistent across languages (US2, SC-005)

Place an equivalent `subphase` heading in two languages' fixture content for the same
edition/revision; generate both.

**Expected**: both PDFs render the heading with the identical background color at the equivalent
content point.

## Success signals

- A `subphase` heading's background is always visibly brighter than a `phase` heading's, at the same
  width/position (SC-001/SC-002).
- Multiple `subphase` headings each render correctly and independently (SC-003).
- `phase` and `subphase` remain distinguishable from each other in print-friendly grayscale mode
  (SC-004).
- Equivalent placement renders the identical background color across languages (SC-005).
- No code changes were needed to add/move/remove a `subphase` heading — only content edits (SC-006).
