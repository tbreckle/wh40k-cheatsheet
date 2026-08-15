# Contract: `page_break` Block & Segmentation

Feature: [spec.md](../spec.md) · Plan: [plan.md](../plan.md) · Data model: [data-model.md](../data-model.md)

The interface content authors and the renderer depend on: how to author a break, and what guarantees
segmentation provides.

---

## Authoring contract

Insert `{type: page_break}` anywhere in `document.blocks`, between two other blocks (or at the
start/end):

```yaml
document:
  blocks:
    - type: phase
      title: "..."
    - type: page_break     # everything after this starts on a new page
    - type: phase
      title: "..."
```

- No other fields are read from a `page_break` block.
- Works identically in every language's `content.yaml` for a shared edition/revision (FR-008) — it
  is authored per-language like the rest of the content, so equivalent placement across languages is
  the author's responsibility, not something the system infers.
- Adding, moving, or deleting a `page_break` entry never requires touching any other block (FR-010).

---

## Rendering contract (`group_by_page_breaks`)

| # | Guarantee | Verified (research.md) |
|---|-----------|:---:|
| G1 | Content before a marker renders exactly as without it (FR-003) | ✅ (segment boundaries don't reorder or alter block content) |
| G2 | Content after a marker starts on a new page (FR-002) | ✅ §2 |
| G3 | A marker at the very start produces no leading blank page (FR-004) | ✅ §3 |
| G4 | A marker at the very end produces no trailing blank page (FR-005) | ✅ §3 |
| G5 | Consecutive markers collapse to one page transition (FR-006) | ✅ §3 |
| G6 | Any number of markers, each independently effective (FR-007) | ✅ §2 (3-segment case) |
| G7 | Content not adjacent to any marker is otherwise unaffected — existing per-element `break-inside: avoid` rules, column flow, etc. still apply within each segment (FR-009) | ✅ (unchanged per-segment CSS) |
| G8 | Page footer (`Page X / Y`) remains correct across segments | ✅ §4 |

---

## Behavioral examples

| `document.blocks` (types only) | Segments produced | Pages |
|---|---|---|
| `[phase, para]` (no markers) | `[[phase, para]]` | 1 |
| `[phase, page_break, para]` | `[[phase], [para]]` | 2 |
| `[page_break, phase, para]` | `[[phase, para]]` | 1 (no leading blank) |
| `[phase, para, page_break]` | `[[phase, para]]` | 1 (no trailing blank) |
| `[phase, page_break, page_break, para]` | `[[phase], [para]]` | 2 (collapsed) |
| `[a, page_break, b, page_break, c]` | `[[a], [b], [c]]` | 3 |

---

## CSS mechanism (implementation detail, documented for traceability)

```css
.sheet { column-count: 2; column-gap: 5mm; }   /* unchanged from feature 002 */
.sheet + .sheet { break-before: page; }         /* new: forces a page break before every
                                                     .sheet that follows another .sheet */
```

One `.sheet` div is rendered per non-empty `Segment`; the adjacent-sibling selector means the first
segment is never affected (nothing precedes it), and every subsequent segment forces its own page.
