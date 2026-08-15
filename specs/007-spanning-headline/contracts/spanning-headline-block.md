# Contract: `spanning_headline` Block

Feature: [spec.md](../spec.md) · Plan: [plan.md](../plan.md) · Data model: [data-model.md](../data-model.md)

The interface content authors and the renderer depend on: how to author a spanning headline, and what
guarantees rendering provides.

---

## Authoring contract

Insert `{type: spanning_headline, title: "..."}` anywhere in `document.blocks`, exactly like `phase`:

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

- `title` is required (the heading text).
- Works identically in every language's `content.yaml` for a shared edition/revision, authored
  per-language like every other block (FR-008).
- Adding, moving, or deleting a `spanning_headline` entry never requires touching any other block or
  any code (FR-009).
- May be placed adjacent to (or far from) `page_break`/`column_reset` markers with no special
  authoring rules — the two feature families don't interact (research.md §2).

---

## Rendering contract

| # | Guarantee | Verified (research.md) |
|---|-----------|:---:|
| G1 | The headline's text and background span the complete two-column width (FR-002) | ✅ §1 (box width ≈ full content width) |
| G2 | Content immediately before renders completely, unaffected, in its normal column position (FR-004) | ✅ §1 (visual render) |
| G3 | Content immediately after resumes in normal column flow beneath the span (FR-005) | ✅ §1 (visual render) |
| G4 | Visually distinguishable from the standard single-column heading (FR-003) | ✅ §3 (width/position difference) |
| G5 | Any number of spanning headlines, each independently correct (FR-006) | ✅ (per-block dispatch, no shared state) |
| G6 | Correct at the very start/end of the document (FR-007) | ✅ (ordinary block dispatch; no segmentation dependency) |
| G7 | Coexists correctly with `page_break`/`column_reset` (FR-010) | ✅ §2 (orthogonal by construction) |
| G8 | Cross-language consistency for equivalent placement (FR-008) | ✅ (pure function of already-resolved per-language content) |

---

## CSS mechanism (implementation detail, documented for traceability)

```css
.phase--spanning { column-span: all; }
```

Applied alongside the existing `.phase` class (`<h2 class="phase phase--spanning">`), reusing its
color/typography/padding — the only new behavior is that the element spans both columns of whichever
`.sheet` (or `.sheet--soft`) container it renders inside.
