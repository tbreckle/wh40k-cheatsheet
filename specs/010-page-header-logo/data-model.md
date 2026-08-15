# Phase 1 Data Model: Page Header Logo — Background Watermark

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md) · Research: [research.md](./research.md)

Same as the original spec: no document-content entity. The watermark is a fixed, unconditional
element of every generated page, not an authored `content.yaml` block.

---

## Entity: Logo Watermark → derived from `images/logo_40k.png`

| Field | Value | Notes |
|-------|-------|-------|
| Source | `images/logo_40k.png`, repository root | Unchanged — version-controlled, sole source asset (FR-008) |
| Source dimensions | 2184×668px, RGBA | Aspect ratio 3.2695:1 — a wide, short rectangle |
| Pre-rotation display size | ≈227.42mm × 69.56mm (644.67pt × 197.18pt) | Computed so the *rotated* bounding box exactly matches the page width (research.md §1) |
| Rotation | 45° | Per Clarifications/FR-002 |
| Rendered shape after rotation | A thin diagonal band (not a wide diamond) | Correct given the source's own extreme aspect ratio (research.md §2) — not a bug |
| Opacity | 0.05 (5%) | Baked in via CSS `opacity`, per FR-004 — tuned down from the originally-clarified 0.3 after visual review |
| Stacking | Behind all other content | Achieved via DOM order alone — no `z-index` (research.md §4) |

**Validation rules**
- MUST exist and be readable before rendering begins (FR-007) — unchanged pre-flight check from the
  original corner-logo implementation (`Paths.images_root`, `_verify_logo_asset`).
- MUST render identically (position, size, rotation, opacity) on every page, regardless of language
  or content (FR-006).
- MUST NOT visually obscure any header/footer/body content — the watermark's low opacity plus
  strictly-behind stacking are what guarantee this (FR-005).

---

## Relationships

```text
images/logo_40k.png (unchanged source asset)
        │
        │ pre-flight existence check (pipeline.py — UNCHANGED from original 010 work)
        ▼
   PdfError if missing → KNOWN_ERRORS → exit 1, no output (FR-007)
        │
        │ present → template renders
        ▼
<img class="page-watermark" src="../images/logo_40k.png">
        │
        │ position: fixed (repeats per page, WeasyPrint-native)
        │ transform: rotate(45deg) (paint-time only, doesn't affect layout box)
        │ opacity: 0.05
        │ DOM order: placed before <article>, so it paints first (behind)
        ▼
Every generated page: a faint, 45°-rotated diagonal watermark behind all content
```

## State / flow

Stateless — identical inputs always produce identical output. No new persistence, no derived data;
purely a CSS/markup change on top of the existing, unchanged Python pipeline.
