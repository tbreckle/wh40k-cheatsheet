# Phase 1 Data Model: Column Reset in Generated Output

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md)

This feature adds one new content-block kind and evolves the derived, rendering-time `Segment`
structure introduced in `005-page-breaks` to carry break-type information. No new persisted
entities.

---

## Entity: Column Reset Point → `column_reset` block

A content-block entry, authored inline in `document.blocks` exactly like `page_break` and every
other block kind.

| Field | Type | Notes |
|-------|------|-------|
| `type` | `"column_reset"` | The only required field; no other fields are meaningful |

**Validation rules**
- Has no visible content of its own (spec Key Entities) — affects segmentation only.
- May appear any number of times, anywhere in `document.blocks` (FR-008).
- Distinct from `page_break`: does not, by itself, force a new page (FR-003).
- When immediately adjacent to a `page_break` marker (no block between them, in either order), the
  combined effect resolves to `page_break`'s behavior (FR-009; research.md §3).

Example:

```yaml
document:
  blocks:
    - type: subsection
      title: "..."
    - type: column_reset
    - type: subsection
      title: "..."          # begins in a left column; same page if room remains
```

---

## Derived structure: `Segment` (evolved from `005-page-breaks`)

Computed at render time by `group_by_breaks(blocks)`; not authored, not persisted.

| Field | Type | Notes |
|-------|------|-------|
| `blocks` | `list[dict]` | A contiguous run of non-marker blocks between two markers (or list boundaries) — unchanged from `005` |
| `break_type` | `"page" \| "soft" \| None` | **New.** `"page"` forces a new page (rendered without the `sheet--soft` class); `"soft"` realigns to the left column without forcing a page (rendered with `sheet--soft`); `None` only for the very first segment when no marker precedes it |

**Derivation algorithm** (single linear pass, per research.md §3–4):

```text
segments = []
current = []
pending = None
for block in blocks:
    if block.type == "page_break":
        if current: segments.append(Segment(current, pending)); current = []
        pending = "page"                      # page_break always wins
    elif block.type == "column_reset":
        if current: segments.append(Segment(current, pending)); current = []
        if pending != "page": pending = "soft"  # column_reset never overrides an already-pending page
    else:
        current.append(block)
if current: segments.append(Segment(current, pending))
return segments
```

**Derivation rules**
1. Split `document.blocks` into runs, using each marker (`page_break` or `column_reset`) as a
   boundary; the marker itself is consumed, not included in either resulting run (unchanged from
   `005`).
2. Discard any run with zero blocks (unchanged from `005` — this is what makes leading, trailing, and
   consecutive markers of *either* type safe).
3. `pending` accumulates across a run of consecutive markers: `page_break` unconditionally sets it to
   `"page"`; `column_reset` sets it to `"soft"` **only if not already `"page"`** — this is the
   priority-merge rule (research.md §3), and it is order-independent by construction.
4. The resulting ordered list of `Segment`s is rendered, each as its own `<div class="sheet">`
   (`break_type == "page"`) or `<div class="sheet sheet--soft">` (`break_type == "soft"`).

**Example**: `[a, column_reset, b, page_break, column_reset, c]` →
`[Segment([a], None), Segment([b], "soft"), Segment([c], "page")]` — the middle marker run
(`page_break, column_reset`) resolves to `"page"` per the priority-merge rule.

---

## Relationships

```text
content.yaml (per edition/revision/language)
   └── document.blocks: [block, block, column_reset, block, page_break, block, ...]

                    │ group_by_breaks() (render-time, pure function; single linear pass)
                    ▼

        [Segment(blocks, break_type=None|"page"|"soft"), ...]      ← derived, never persisted

                    │ template render:
                    │   break_type == "page" → <div class="sheet">
                    │   break_type == "soft" → <div class="sheet sheet--soft">
                    ▼

        HTML with N sibling .sheet containers, some marked --soft
                    │ CSS:
                    │   .sheet + .sheet { break-before: page; }              (005, unchanged)
                    │   .sheet + .sheet.sheet--soft { break-before: auto; }  (new, overrides)
                    ▼

        PDF: "page" segments always start a new page; "soft" segments start in a left
        column on the same page if room remains, or naturally overflow if not
        (research.md §1–2, verified empirically)
```

## State / flow

Segmentation remains a stateless, pure transform of `document.blocks` — same inputs always yield the
same segments, break types, and page layout. No new state, no new persistence, consistent with the
stateless pipeline design established in `002-pdf-generation` and `005-page-breaks`.
