# Phase 1 Data Model: Full-Width Spanning Headline

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md)

This feature adds one new visible content-block kind. No changes to any derived structure — unlike
`005-page-breaks`/`006-column-reset`, this block never participates in segmentation (research.md §2).

---

## Entity: Spanning Headline → `spanning_headline` block

A content-block entry, authored inline in `document.blocks` exactly like the existing `phase` block.

| Field | Type | Notes |
|-------|------|-------|
| `type` | `"spanning_headline"` | Required |
| `title` | `str` | The heading text, required — same authoring shape as `phase.title` |

**Validation rules**
- Carries visible content (its own title text) — unlike `page_break`/`column_reset`, it is not a
  structural-only marker (spec Assumptions).
- May appear any number of times, anywhere in `document.blocks` (FR-006).
- Renders identically regardless of which segment (page-forced, soft-reset, or default) it falls
  into — it is dispatched by `render_block` the same way as every other visible block type
  (research.md §2).
- Has no interaction with `page_break`/`column_reset` markers at the data level — they may appear
  adjacent to a `spanning_headline` with no special handling required.

Example:

```yaml
document:
  blocks:
    - type: subsection
      title: "..."
    - type: spanning_headline
      title: "NEW MAJOR SECTION"
    - type: subsection
      title: "..."
```

---

## Entity: Glossary (extended, `002-pdf-generation`) — 2026-08-14 addition

Gains one optional field, following the same per-block-type flag convention already used elsewhere
(e.g., `callout.variant`, `stratagem.timing`).

| Field | Type | Notes |
|-------|------|-------|
| `spanning` | `bool` | Optional, defaults to falsy/absent. When truthy, both the glossary's title bar and its term-list div render with the same full-width treatment as `spanning_headline` (FR-011, amended 2026-08-15). The term *content* is unaffected regardless. |

**Validation rules**
- Absent or falsy → identical rendering to before this addition (no behavior change for existing
  content, including the real `11e` glossary block).
- Truthy → the glossary's `<h2>` title gains the `phase--spanning` class, and its
  `<div class="glossary">` term list gains a `glossary--spanning` class — both span full width
  (2026-08-15 fix; originally title-bar only per Clarifications 2026-08-14, which turned out to
  fragment long term lists into 4 visible columns instead of 2). Term content itself is unchanged.

---

## Relationships

```text
content.yaml (per edition/revision/language)
   └── document.blocks: [block, block, spanning_headline, block, ...]

                    │ group_by_breaks() — UNCHANGED from 006, spanning_headline is not a marker
                    ▼

        [Segment(blocks=[..., spanning_headline_block, ...], break_type=...), ...]

                    │ template render — render_block() dispatches spanning_headline
                    │ like any other visible block, within whichever .sheet it's in
                    ▼

        <div class="sheet">
          ...
          <h2 class="phase phase--spanning">NEW MAJOR SECTION</h2>   ← column-span: all
          ...
          <h2 class="phase[ phase--spanning]">CORE ABILITIES</h2>    ← glossary title,
          <div class="glossary">...</div>                             class conditional on
                                                                        block.spanning (2026-08-14)
        </div>
```

## State / flow

Stateless, pure rendering — identical inputs always produce identical output. No new persistence, no
new derived structure; this is purely an additional branch in the existing `render_block` dispatch.
