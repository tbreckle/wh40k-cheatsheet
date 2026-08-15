# Quickstart: Page Header Logo — Background Watermark

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md) ·
Contract: [contracts/page-logo.md](./contracts/page-logo.md)

Validates the watermark's presence, rotation, opacity, sizing, and fail-loud behavior end-to-end on
top of the existing `002`–`009` generator. Assumes the implementation task has updated the
`.page-watermark` CSS rule, the `@page` margin, and the `<img>` placement in
`templates/cheatsheet.html.j2`. The Python pre-flight check is unchanged from the original
corner-logo work.

## Prerequisites

Same as features 002–009: `uv sync`, WeasyPrint native libraries installed, `project.yaml` present,
`images/logo_40k.png` present at the repository root.

## Validation scenarios

### Scenario 1 — Watermark appears on every page, correctly styled (US1, SC-001/SC-002/SC-003)

```bash
uv run wh40k-cheatsheet generate --edition 11e
```

**Expected**: every page of both the `en` and `de` PDFs shows a faint, 45°-rotated diagonal
watermark behind the content — visually distinct from a corner badge, subtle enough to read as "very
light" branding rather than a dominant graphic.

### Scenario 2 — Text stays fully readable over the watermark (US1, FR-005/SC-004)

Inspect pages with dense content (e.g. the stratagem cards page) where the watermark passes directly
behind text.

**Expected**: all text remains fully legible; the watermark never darkens or visually competes with
any header, footer, or body content.

### Scenario 3 — Consistent across pages and languages (US1, FR-006)

Compare the watermark's position/size/rotation/opacity across all pages of both language editions.

**Expected**: identical on every page, in both `en` and `de`.

### Scenario 4 — Existing content otherwise unaffected (SC-005)

Compare page counts of the regenerated `11e` output against the pre-amendment baseline (3 pages
`en`, 4 pages `de`).

**Expected**: unchanged — the only visible difference is the corner logo becoming a background
watermark.

### Scenario 5 — Missing logo asset still fails loudly (F1, FR-007)

Temporarily rename or remove `images/logo_40k.png`, then attempt generation; restore the file
afterward.

```bash
mv images/logo_40k.png images/logo_40k.png.bak
uv run wh40k-cheatsheet generate --edition 11e; echo "exit: $?"
mv images/logo_40k.png.bak images/logo_40k.png
```

**Expected**: generation fails with a clear message naming the expected logo path, a non-zero exit
code, and no PDF is written — this behavior is inherited unchanged from the original implementation.

## Success signals

- The watermark appears on 100% of generated pages, faint and diagonal, not in a corner (SC-001).
- Rotation is 45° and opacity is ≈5% on every page (SC-002).
- The watermark is fully visible with no cropping, at the largest size that fits the page (SC-003).
- All existing content remains fully readable — the watermark never obscures it (SC-004).
- Regenerating existing content changes nothing except corner logo → background watermark (SC-005).
- A missing logo asset is impossible to miss — generation fails clearly, not silently (FR-007).
