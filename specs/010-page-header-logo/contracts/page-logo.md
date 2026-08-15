# Contract: Page Background Watermark

Feature: [spec.md](../spec.md) · Plan: [plan.md](../plan.md) · Data model: [data-model.md](../data-model.md)

Supersedes the original top-right-corner contract. Not an authoring contract — the watermark is
unconditional, with no content-block flag to set.

---

## Rendering contract

| # | Guarantee | Basis |
|---|-----------|-------|
| G1 | The watermark appears behind every generated page's content, not in a page corner | `position: fixed` `<img>`, repeated per page by WeasyPrint; DOM order places it before all other body content so it paints behind (FR-001; research.md §1/§4) |
| G2 | The watermark is rotated 45° | `transform: rotate(45deg)` (FR-002; SC-002) |
| G3 | The watermark is scaled as large as possible while remaining fully visible within the page bounds after rotation, aspect ratio preserved | Pre-rotation size ≈227.42×69.56mm, computed so the rotated (square) bounding box exactly matches the page width — verified empirically (FR-003; SC-003; research.md §1) |
| G4 | The watermark renders at ≈5% opacity | `opacity: 0.05` (FR-004; SC-002) |
| G5 | The watermark never obscures existing header, footer, or body content | Strictly-behind stacking (no `z-index`) + low opacity, verified against real content in both languages with all text remaining readable (FR-005; SC-004) |
| G6 | The watermark appears identically (position, size, rotation, opacity) on every page, regardless of language or content | Verified: same rendered position on every page of the real `11e` content in both `en` and `de` (FR-006) |

---

## Failure-mode contract

| # | Guarantee | Basis |
|---|-----------|-------|
| F1 | If `images/logo_40k.png` is missing or unreadable, generation fails with a clear message naming the expected path — no PDF is emitted | Unchanged pre-flight existence check from the original corner-logo implementation (`Paths.images_root`, `pipeline._verify_logo_asset`) — this contract item and its enforcement mechanism are untouched by this amendment (FR-007) |

---

## CSS mechanism (implementation detail, documented for traceability)

```css
@page {
  margin: 7mm 6mm 8mm 6mm;   /* reverted to the original margin — no longer needs enlarging */
}
.page-watermark {
  position: fixed;
  left: -14.71mm;    /* content-box-relative; accounts for the @page left margin */
  top: 106.72mm;      /* content-box-relative; accounts for the @page top margin */
  width: 227.42mm;
  height: 69.56mm;
  transform: rotate(45deg);
  opacity: 0.05;
  /* no z-index — DOM order alone puts this behind subsequent content; a negative
     z-index was tested and found to hide the watermark entirely (research.md §4) */
}
```

```html
<img class="page-watermark" src="../images/logo_40k.png" alt="">
```

Placed once, immediately after `<body>`, before the document's own content — WeasyPrint's
`position: fixed` handling repeats it on every page automatically, unchanged mechanism from the
original corner-logo implementation.

### Sizing derivation (for future maintenance)

For a rectangle `w × h` rotated 45°, the rotated bounding box is a square with side
`(w + h) × cos(45°)`. Solving for that side to equal the page's width (595.28pt, the binding
constraint for A4 portrait) and the logo's own aspect ratio (2184:668 ≈ 3.2695):

```text
w = (page_width / cos(45°)) / (1 + 1/aspect_ratio) ≈ 644.67pt (227.42mm)
h = w / aspect_ratio ≈ 197.18pt (69.56mm)
```

If the source logo image is ever replaced with a different aspect ratio, these two values (and the
derived `left`/`top` offsets) need recomputing with the same formula.
