# Contract: List Single-Column (Full-Width) Flag

Feature: [spec.md](../spec.md) · Plan: [plan.md](../plan.md) · Data model: [data-model.md](../data-model.md)

Extends the existing `list` block (`002-pdf-generation`) with an optional flag that gives it the
document's full page width, reusing the mechanism proven in `007-spanning-headline`.

---

## Authoring contract

Add `single_column: true` to an existing `list` block:

```yaml
document:
  blocks:
    - type: list
      single_column: true          # optional; defaults to off
      items:
        - "A long item that reads better across the full page width"
        - {text: "An item with sub-items", sub: ["detail one", "detail two"]}
```

- `single_column` is optional and defaults to off (falsy/absent) — every `list` block that doesn't
  set it renders exactly as it did before this feature.
- Every other field (`items`, and each item's `text`/`html`/`sub`) behaves exactly as documented in
  `002-pdf-generation` — the flag changes only the outer column width, nothing about item content or
  styling.

---

## Rendering contract

| # | Guarantee | Basis |
|---|-----------|-------|
| G1 | `single_column: true` makes the list render across the complete width of both of the sheet's columns (FR-001) | `column-span: all` on the new `.block--full-width` class, verified empirically in research.md §1 |
| G2 | The list's item markup — including nested `sub` items — is byte-for-byte identical whether `single_column` is set or not, aside from the wrapper `div`'s class | `render_list`'s own macro output is untouched by this addition (FR-003) |
| G3 | Omitting `single_column` (or setting it falsy) preserves the exact pre-existing `list` rendering — no regression for content authored before this addition (FR-002) | Conditional class application only; no change to the default path |
| G4 | Coexists correctly with `page_break`/`column_reset`, exactly as the `list` block already does (FR-004) | The list block is dispatched the same way regardless of `single_column`; no new interaction surface (research.md §3) |
| G5 | Content immediately before and after a flagged list renders completely and in correct reading order (FR-003, SC-002) | `column-span: all` operates within the existing multicol flow; verified empirically in research.md §1 |

---

## CSS mechanism (implementation detail, documented for traceability)

```text
<div class="block{{ ' block--full-width' if block.single_column | default(false) else '' }}">
```

`.block--full-width { column-span: all; }` — a new rule, mechanically identical to
`h2.phase--spanning { column-span: all; }` from `007-spanning-headline`, applied to the `list`
block's own wrapper element instead of a heading.
