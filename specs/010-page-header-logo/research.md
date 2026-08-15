# Phase 0 Research: Page Header Logo — Background Watermark Amendment

Feature: [spec.md](./spec.md)

This supersedes the original top-right-corner research — the mechanism changed entirely (a
full-page, 45°-rotated background watermark instead of a small corner badge; opacity was
originally clarified at 30% and later tuned down to 5% per direct follow-up request). All
findings below are verified empirically against the actually-installed WeasyPrint and the real
`11e` content, following this project's established discipline.

---

## 1. Sizing: the rotated bounding box is a square; page width is the binding constraint

**Decision**: Reuse the same `<img>` + `position: fixed` mechanism from the original corner logo —
it already handles per-page repetition correctly (research from the original 010 spec, unchanged).
Compute the pre-rotation image dimensions so the ROTATED bounding box exactly matches the page's
width (the binding constraint for A4 portrait, since width < height).

**Rationale**: For a rectangle of width `w` and height `h` rotated 45°, the rotated bounding box is
always a **square** with side `(w + h) × cos(45°)`, regardless of the rectangle's own aspect ratio —
elementary rotation geometry, confirmed against the actual render. Since A4 portrait's width
(595.28pt) is smaller than its height (841.89pt), the width is the binding constraint for "fits
entirely within the page, nothing cropped" (per Clarifications). Solving for the logo's own 3.2695:1
aspect ratio: pre-rotation width ≈ 644.67pt (227.42mm), height ≈ 197.18pt (69.56mm) — verified this
produces a rotated bounding box of exactly 595.28pt (matching page width) by direct calculation and
by rendering.

---

## 2. A wide, short logo rotated 45° looks like a thin diagonal band — this is correct, not a bug

**Decision**: Accept this as the correct, intended visual. Do not attempt to "widen" the rotated
footprint artificially.

**Rationale**: This is worth recording because it cost significant investigation time. The source
logo (`images/logo_40k.png`) is 2184×668px — a very wide, short rectangle (3.27:1). Rotating a
shape with an extreme aspect ratio by 45° produces an elongated, narrow parallelogram (think of a
yardstick spun 45° — it becomes a thin diagonal line, not a wide diamond), **not** a bold,
wide "X"-shaped watermark. Several rendering approaches were tried while (incorrectly) suspecting a
WeasyPrint/Pillow clipping bug — CSS `transform: rotate()` on an `<img>`, a `<div>` with
`background-image`, and a Pillow-pre-rotated static PNG all independently produced the **same**
diagonal-band shape. That consistency, across three unrelated rendering paths, was the signal that
this is the image's actual correct rotated geometry, not a shared bug. Direct pixel-level inspection
of the Pillow-rotated result confirmed dense content really does only occupy a narrow diagonal band
within the square canvas — nothing is being cropped. Given the spec's own goal ("only be shown very
light," a subtle brand mark, not a dominant graphic), a slim diagonal watermark band is arguably a
*better* fit for the request than a bold filled diamond would have been.

**Alternatives considered**: Padding the source image with transparent margins to force a "fatter"
rotated footprint — rejected; not requested, and would require maintaining a modified copy of the
source asset, contradicting FR-008's single-source-of-truth requirement.

---

## 3. `position: fixed`'s containing block is the content box — same finding as before, reapplied

**Decision**: Same technique as the original corner-logo research (§2b there): compute `left`/`top`
as absolute lengths relative to the content box, accounting for the `@page` margins, rather than
using percentage-based centering (which resolves against the *content* box's dimensions, not the
full physical page — an easy source of off-by-margin errors).

**Rationale**: Re-confirmed empirically: `position: fixed`'s containing block remains the content
box (inside the `@page` margins), not the physical page edge, unchanged from the original research.
The **top margin no longer needs enlarging** for this design (unlike the original corner logo) —
the watermark sits low enough on the page, and reaching into the margin band the way the corner logo
needed to is unnecessary here; the `@page` margin reverts to its original `7mm 6mm 8mm 6mm`.

---

## 4. `z-index` is unnecessary — and a naive negative value hides the watermark entirely

**Decision**: Do **not** set `z-index` on the watermark. Rely on DOM/paint order alone: the `<img>`
is placed once, immediately after `<body>`, before the document's own content — this alone makes it
paint first (behind) with all subsequent static content painting over it.

**Rationale**: An initial attempt added `z-index: -1` on the assumption that this would be "extra
safe" for keeping the watermark behind text. It instead made the watermark **invisible entirely** —
confirmed by testing at full opacity with an opaque red background, which still showed nothing.
`position: fixed` elements without an explicit `z-index` (or with `z-index: auto`) already paint
above normal-flow, non-positioned static content per standard CSS stacking rules — DOM order alone
is sufficient and correct here. `z-index: -1` instead pushed the watermark **behind the page's own
canvas background**, since the page background paints at the very bottom of the whole stack — a trap
worth avoiding in any future "sits behind content" layering on this template.

---

## 5. FR-007 (fail-loud on a missing logo) needs no changes

**Decision**: The pre-flight existence check added for the original corner-logo feature
(`Paths.images_root`, `_verify_logo_asset` in `pipeline.py`) is reused unchanged.

**Rationale**: That check verifies `images/logo_40k.png` exists before rendering, independent of how
the logo is subsequently displayed in the template. Since this amendment only changes the template's
CSS/markup (not which file is referenced), the existing check and its tests remain fully valid and
require no modification.

---

## Resolved unknowns summary

| Unknown | Resolution |
|---------|------------|
| Full-page sizing math | Rotated bounding box is a square; page width is the binding constraint; pre-rotation size ≈ 227.42mm × 69.56mm |
| Visual shape after rotation | A thin diagonal band, not a wide diamond — correct given the logo's own 3.27:1 aspect ratio, not a bug |
| Positioning coordinate system | Same as original research — content-box-relative, needs margin-aware absolute offsets |
| `@page` top margin | Reverts to original `7mm` — no longer needs enlarging for this design |
| Stacking/z-index | None needed; DOM order alone puts the watermark behind content; `z-index: -1` is a trap that hides it entirely |
| Fail-loud missing-asset behavior | Unchanged — the existing pipeline check already covers this regardless of display mechanism |

No open NEEDS CLARIFICATION items remain.
