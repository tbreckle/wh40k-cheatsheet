# Contract: `subphase` Block

Feature: [spec.md](../spec.md) · Plan: [plan.md](../plan.md) · Data model: [data-model.md](../data-model.md)

The interface content authors and the renderer depend on: how to author a subphase heading, and what
guarantees rendering provides.

---

## Authoring contract

Insert `{type: subphase, title: "..."}` anywhere in `document.blocks`, exactly like `phase`:

```yaml
document:
  blocks:
    - type: phase
      title: "1. COMMAND PHASE"
    - type: subphase
      title: "1a. Battle-shock Step"
```

- `title` is required (the heading text).
- Works identically in every language's `content.yaml` for a shared edition/revision, authored
  per-language like every other block (FR-007).
- Adding, moving, or deleting a `subphase` entry never requires touching any other block or any code
  (FR-008).
- Does not require a preceding `phase` block — it renders correctly on its own, including at the very
  start or end of a document (FR-006).
- May be placed adjacent to (or far from) `page_break`/`column_reset` markers with no special
  authoring rules — the two feature families don't interact.

---

## Rendering contract

| # | Guarantee | Verified (research.md) |
|---|-----------|:---:|
| G1 | Renders using the same typography, padding, and width as a `phase` heading (FR-002) | ✅ §1 (shared `.phase` base styling) |
| G2 | Background is a visibly brighter shade than `phase`'s, in the same green color family (FR-003) | ✅ §2 (dedicated `--green-subphase` custom property) |
| G3 | Content immediately before/after renders completely, unaffected, in normal column position (FR-006) | ✅ (ordinary block dispatch; no segmentation dependency) |
| G4 | Any number of `subphase` headings, each independently correct (FR-005) | ✅ (per-block dispatch, no shared state) |
| G5 | In print-friendly mode, resolves to a grayscale shade distinct from `phase`'s (FR-004) | ✅ §3 (distinct grayscale value) |
| G6 | Coexists correctly with `page_break`/`column_reset` (FR-009) | ✅ (orthogonal by construction, same as `spanning_headline`) |
| G7 | Cross-language consistency for equivalent placement (FR-007) | ✅ (pure function of already-resolved per-language content) |

---

## CSS mechanism (implementation detail, documented for traceability)

```css
:root {
  --green-subphase: #256b46; /* #3d3d3d in print-friendly mode */
}

h2.phase--sub {
  background: var(--green-subphase);
}
```

Applied alongside the existing `.phase` class (`<h2 class="phase phase--sub">`), reusing its
typography/padding/width — the only new behavior is a brighter `background-color`, overriding
`.phase`'s `var(--green-dark)` for elements that also carry `.phase--sub` (equal specificity, later
source order wins).
