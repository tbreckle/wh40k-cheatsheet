# Phase 1 Data Model: Subphase Heading

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md)

This feature adds one new visible content-block kind. No changes to any derived structure — like
`007-spanning-headline`, this block never participates in segmentation (research.md §1).

---

## Entity: Subphase Heading → `subphase` block

A content-block entry, authored inline in `document.blocks` exactly like the existing `phase` block.

| Field | Type | Notes |
|-------|------|-------|
| `type` | `"subphase"` | Required |
| `title` | `str` | The heading text, required — same authoring shape as `phase.title` |

**Validation rules**
- Carries visible content (its own title text) — unlike `page_break`/`column_reset`, it is not a
  structural-only marker.
- May appear any number of times, anywhere in `document.blocks` (FR-005), independently of whether a
  `phase` block precedes it.
- Renders identically regardless of which segment (page-forced, soft-reset, or default) it falls
  into — it is dispatched by `render_block` the same way as every other visible block type
  (research.md §1).
- Has no interaction with `page_break`/`column_reset` markers at the data level — they may appear
  adjacent to a `subphase` with no special handling required.

Example:

```yaml
document:
  blocks:
    - type: phase
      title: "1. COMMAND PHASE"
    - type: subphase
      title: "1a. Battle-shock Step"
```

---

## CSS custom property: `--green-subphase`

Follows the existing `:root` custom-property pattern from `002-pdf-generation`/`011-print-friendly-pdf`.

| Property | Light-mode value | Print-friendly (grayscale) value | Notes |
|----------|-------------------|-----------------------------------|-------|
| `--green-subphase` | `#256b46` | `#3d3d3d` | Brighter than `--green-dark` (`#1e4d34` / `#262626`) in both modes, keeping `phase`/`subphase` distinguishable in print-friendly output (FR-004) |

---

## Relationships

```text
content.yaml (per edition/revision/language)
   └── document.blocks: [phase, subphase, block, ...]

                    │ group_by_breaks() — UNCHANGED, subphase is not a marker
                    ▼

        [Segment(blocks=[..., subphase_block, ...], break_type=...), ...]

                    │ template render — render_block() dispatches subphase
                    │ like any other visible block, within whichever .sheet it's in
                    ▼

        <div class="sheet">
          ...
          <h2 class="phase">1. COMMAND PHASE</h2>          ← background: var(--green-dark)
          <h2 class="phase phase--sub">1a. Battle-shock Step</h2>  ← background: var(--green-subphase)
          ...
        </div>
```

## State / flow

Stateless, pure rendering — identical inputs always produce identical output. No new persistence, no
new derived structure; this is purely an additional branch in the existing `render_block` dispatch,
plus one new CSS custom property.
