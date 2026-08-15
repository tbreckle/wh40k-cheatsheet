# Phase 1 Data Model: List Single-Column (Full-Width) Flag

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md)

This feature adds one optional field to an existing content-block kind. No changes to any derived
structure — like `spanning_headline`, this flag never participates in segmentation
(research.md §3).

---

## Entity: List (extended, `002-pdf-generation`)

Gains one optional field, following the same per-block-type flag convention already used elsewhere
(e.g., `glossary.spanning`, `callout.variant`, `stratagem.timing`).

| Field | Type | Notes |
|-------|------|-------|
| `single_column` | `bool` | Optional, defaults to falsy/absent. When truthy, the list renders across the complete width of both of the sheet's columns instead of being confined to one (FR-001). |

**Validation rules**
- Absent or falsy → identical rendering to before this feature (no behavior change for existing
  content, including any real `11e` `list` blocks).
- Truthy → the list's wrapper `<div class="block">` gains the `block--full-width` class; the
  `render_list` macro's own output (including any nested `sub` items) is otherwise unchanged
  (FR-003).
- Has no interaction with `page_break`/`column_reset` markers at the data level — they may appear
  adjacent to a flagged list with no special handling required (FR-004; research.md §3).

Example:

```yaml
document:
  blocks:
    - type: subsection
      title: "..."
    - type: list
      single_column: true
      items:
        - "A long item that reads better across the full page width"
        - "Another item"
    - type: subsection
      title: "..."
```

---

## Relationships

```text
content.yaml (per edition/revision/language)
   └── document.blocks: [block, block, list, block, ...]

                    │ group_by_breaks() — UNCHANGED, list is not a marker
                    ▼

        [Segment(blocks=[..., list_block, ...], break_type=...), ...]

                    │ template render — render_block() dispatches the list branch
                    │ like any other visible block, within whichever .sheet it's in
                    ▼

        <div class="sheet">
          ...
          <div class="block[ block--full-width]">   ← class conditional on
            <ul>...</ul>                               block.single_column
          </div>
          ...
        </div>
```

## State / flow

Stateless, pure rendering — identical inputs always produce identical output. No new persistence, no
new derived structure; this is purely an additional conditional class in the existing `render_block`
dispatch.
