# Phase 1 Data Model: Page Breaks in Generated Output

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md)

This feature adds one new content-block kind and one derived, rendering-time structure. No new
persisted entities beyond what `002-pdf-generation` already defines (content lives in `content.yaml`
per (edition, revision, language), per feature 003's convention).

---

## Entity: Page Break Point → `page_break` block

A content-block entry, authored inline in `document.blocks` exactly like any other block kind.

| Field | Type | Notes |
|-------|------|-------|
| `type` | `"page_break"` | The only required field; no other fields are meaningful |

**Validation rules**
- Has no visible content of its own (spec Key Entities) — the renderer emits no markup for it
  directly; it only affects segmentation (FR-001, FR-010).
- May appear any number of times, anywhere in `document.blocks` (FR-007).
- A `page_break` immediately preceded or followed by another `page_break` (no other block between
  them) collapses to a single segmentation boundary — see `Segment` below (FR-006).

Example (inline with existing blocks, per `editions/11e/2026-08-01-00/{en,de}/content.yaml`
convention):

```yaml
document:
  blocks:
    - type: phase
      title: "4. CHARGE PHASE"
    - type: page_break
    - type: phase
      title: "5. FIGHT PHASE"
```

---

## Derived structure: `Segment`

Computed at render time by `group_by_page_breaks(blocks)` (research.md §5); not authored, not
persisted — purely a rendering-time grouping of the author's `document.blocks`.

| Field | Type | Notes |
|-------|------|-------|
| `blocks` | `list[dict]` | A contiguous run of non-`page_break` blocks between two markers (or list boundaries) |

**Derivation rules**
1. Split `document.blocks` into runs, using each `page_break` block as a boundary (the marker itself
   is consumed, not included in either resulting run).
2. Discard any run with zero blocks (FR-004/FR-005/FR-006 — this is what makes leading, trailing, and
   consecutive markers safe).
3. The resulting ordered list of non-empty runs is the list of `Segment`s rendered, each as its own
   `<div class="sheet">` (research.md §2).

**Example**: `[phase, subsection, page_break, phase, page_break, page_break, table]` →
`[[phase, subsection], [phase], [table]]` — three segments, i.e. three pages' worth of top-level
containers (research.md §3 confirms the double-marker in the middle collapses correctly).

---

## Relationships

```text
content.yaml (per edition/revision/language, feature 002/003 convention)
   └── document.blocks: [block, block, page_break, block, ...]   ← authored, ordered

                    │ group_by_page_breaks() (render-time, pure function)
                    ▼

        [Segment(blocks=[...]), Segment(blocks=[...]), ...]      ← derived, never persisted

                    │ template render (one <div class="sheet"> per Segment)
                    ▼

        HTML with N sibling .sheet containers  ──WeasyPrint──►  PDF with N page transitions
        (.sheet + .sheet { break-before: page })                (research.md §2/§4 verified)
```

## State / flow

Segmentation is a stateless, pure transform of the existing `document.blocks` list — same inputs
always yield the same segments and the same page count. No new state, no new persistence, consistent
with the stateless pipeline design established in `002-pdf-generation`.
