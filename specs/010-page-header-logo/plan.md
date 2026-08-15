# Implementation Plan: Page Header Logo — Background Watermark

**Branch**: `010-page-header-logo` | **Date**: 2026-08-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/010-page-header-logo/spec.md` (amended 2026-08-14 —
background watermark instead of top-right corner)

## Summary

Replace the existing top-right corner logo with a large, faint (5% opacity), 45°-rotated background
watermark behind every generated page's content. Research (research.md) resolved the geometry: a
rotated rectangle's bounding box is always a square, so the pre-rotation image is sized at
≈227.42×69.56mm — computed so the rotated square exactly matches the page's width (the binding
constraint for A4 portrait). A significant investigation initially (incorrectly) suspected a
WeasyPrint/Pillow image-rotation clipping bug; it turned out the logo's own extreme 3.27:1 aspect
ratio naturally produces a thin diagonal band when rotated 45°, not a bold "X" shape — confirmed
correct, not a bug, across three independently-tested rendering approaches. The mechanism itself
(`<img>` + `position: fixed`, repeating per page) and the fail-loud missing-asset guarantee are both
reused unchanged from the original corner-logo implementation — only the CSS (size, rotation,
opacity, and no-longer-needed margin enlargement) and the HTML placement change. This remains a
template-only change; the Python pre-flight check requires no modification.

## Technical Context

**Language/Version**: Python 3.12+ (shared with features 001–009; no change)

**Primary Dependencies**: None new — pure CSS/template change on the existing Jinja2/WeasyPrint
stack. (A Pillow-based pre-rotation workaround was investigated and built during research but
discarded once the "bug" was found to be a misunderstanding, not a real limitation — no new
dependency is introduced.)

**Storage**: N/A — `images/logo_40k.png` remains the sole, unmodified, version-controlled source
asset (FR-008, unchanged from the original spec).

**Testing**: pytest. Integration tests assert the watermark's rotation (45°), opacity (≈0.05), size
(bounding-box fit within the page, source aspect ratio preserved), consistent position across pages
and languages, that it never visually front-runs (obscures) other content, and that the existing
missing-asset fail-loud test still passes unchanged. Following the box-inspection methodology
established in prior features — extended here since a CSS `transform: rotate()` doesn't change a
box's reported layout dimensions (transforms are paint-time only), so tests assert against the
*pre-transform* box size/position and independently verify the rotation/opacity via rendered pixel
sampling where geometry alone isn't sufficient.

**Target Platform**: Same as features 001–009 — local dev + CI (Linux), WeasyPrint-rendered PDF.

**Project Type**: Single project. Touches only `templates/cheatsheet.html.j2` (CSS + `<img>`
placement/class change). `src/wh40k_cheatsheet/pipeline.py` and `cli.py` (the `Paths.images_root`
field and pre-flight check from the original corner-logo work) are **unchanged** — still correct as
they stand.

**Performance Goals**: Same single small PNG, referenced once, repeated per page by WeasyPrint's
native mechanism; no measurable change to generation time.

**Constraints**: Must not alter rendering for any existing content beyond the corner-logo →
watermark swap (SC-005). Must never obscure existing header/footer/body content (FR-005/SC-004) —
verified by DOM-order-only stacking (no `z-index`, which was found to hide the watermark entirely
if set negative — research.md §4). Must preserve the existing fail-loud guarantee for a missing
logo asset (FR-007) — already satisfied, no code change needed.

**Scale/Scope**: One CSS rule replaced (`.page-logo` → `.page-watermark`: new size, `transform:
rotate(45deg)`, `opacity: 0.05`, reverted `@page` margin), one `<img>` class/position change in the
template body. No Python changes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment |
|-----------|------------|
| I. Code Quality | **Satisfied.** Template-only CSS/markup change; no new Python code, no new complexity. |
| II. Testing Standards (NON-NEGOTIABLE) | **Satisfied by design.** Tests assert rotation, opacity, sizing, position-consistency, and non-obscuring against the real content — plus the existing fail-loud test continues to pass unmodified, confirmed by design review. |
| III. User Experience Consistency | **Directly served.** A consistent, subtle, non-intrusive brand watermark on every page is exactly the predictability this principle asks for; explicit care (research.md §4) was taken to guarantee text stays fully readable. |
| IV. Performance Requirements | **Satisfied.** No new work per page; same single image reference. |
| Additional Constraints & Standards | **Satisfied.** No new dependency; `images/logo_40k.png` remains the single source asset. |
| Development Workflow & Quality Gates | **Satisfied.** Ships through the same PR-gated `poe check` workflow, including `008`'s docstring gate (no Python changes here, so no new surface for it). |

**Verdict**: PASS. No violations; Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/010-page-header-logo/
├── plan.md               # This file (rewritten for the watermark amendment)
├── research.md            # Phase 0 output (rewritten — geometry + z-index findings)
├── data-model.md          # Phase 1 output (rewritten)
├── quickstart.md          # Phase 1 output (rewritten)
├── contracts/
│   └── page-logo.md       # Rewritten rendering contract
└── tasks.md                 # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root) — changes to existing files

```text
templates/cheatsheet.html.j2
    # CHANGED:
    #  - @page margin reverts: 15mm 6mm 8mm 6mm → 7mm 6mm 8mm 6mm (no longer needs
    #    enlarging; the watermark doesn't live in the margin band)
    #  - CSS rule replaced: `.page-logo` (corner, 50px height) → `.page-watermark`
    #    (227.42mm × 69.56mm, `transform: rotate(45deg)`, `opacity: 0.05`, no z-index)
    #  - the <img> tag's class and position changes accordingly; still placed once,
    #    immediately after <body>, repeated per page by WeasyPrint automatically
    #  - header doc comment updated to describe the watermark behavior

src/wh40k_cheatsheet/pipeline.py, src/wh40k_cheatsheet/cli.py
    # UNCHANGED — Paths.images_root and the pre-flight existence check already
    # satisfy FR-007 regardless of how the logo is displayed

tests/integration/test_page_logo_pdf.py
    # REWRITTEN: presence/rotation/opacity/aspect-ratio/position-consistency/
    # non-obscuring assertions replace the old corner-position assertions;
    # the missing-asset fail-loud tests are retained essentially unchanged
```

**Structure Decision**: Template-only, same as `007`/`009` — no Python code touched. The Phase 0
research this time required substantially more empirical verification than usual (three independent
rendering approaches tested before confirming there was no bug), which is why research.md is more
detailed than most; the resulting implementation is still minimal.

## Complexity Tracking

> No constitution violations. Section intentionally left empty.
