# Contract: `column_reset` Block & Break-Type Segmentation

Feature: [spec.md](../spec.md) · Plan: [plan.md](../plan.md) · Data model: [data-model.md](../data-model.md)

The interface content authors and the renderer depend on: how to author a column reset, how it
differs from `005-page-breaks`'s `page_break`, and what happens when the two are combined.

---

## Authoring contract

Insert `{type: column_reset}` anywhere in `document.blocks`, exactly like `page_break`:

```yaml
document:
  blocks:
    - type: subsection
      title: "..."
    - type: column_reset     # everything after this starts in a left column — same page if room
    - type: subsection
      title: "..."
```

- No other fields are read from a `column_reset` block.
- Works identically in every language's `content.yaml` for a shared edition/revision, authored
  per-language like `page_break` (FR-010).
- Adding, moving, or deleting a `column_reset` entry never requires touching any other block
  (FR-011).

---

## `column_reset` vs. `page_break` — the difference this contract guarantees

| | `page_break` (`005`) | `column_reset` (this feature) |
|---|---|---|
| Forces a new page | Always | Only if the current page has no room left |
| Guarantees left column | Yes (every new page starts at column 1) | Yes (its own guarantee, independent of paging) |
| Use when | You want a deliberate, unconditional page boundary | You want realignment without wasting space |

---

## Rendering contract (`group_by_breaks`)

| # | Guarantee | Verified (research.md) |
|---|-----------|:---:|
| G1 | Content before a `column_reset` renders exactly as without it (FR-004) | ✅ (segment boundaries don't reorder or alter block content) |
| G2 | Content after a `column_reset` begins in a left column (FR-002) | ✅ §2 (box-position inspection) |
| G3 | A `column_reset` does not force a new page when room remains (FR-003) | ✅ §1–2 |
| G4 | A `column_reset` naturally overflows to the next page (still landing left-column) when the current page is full | ✅ §2 |
| G5 | A marker at the very start produces no altered output (FR-005) | ✅ (inherits `005`'s "no preceding sibling → selector never matches" mechanism) |
| G6 | A marker at the very end produces no trailing blank space (FR-006) | ✅ (inherits `005`'s empty-segment-dropping) |
| G7 | Consecutive `column_reset` markers collapse to one reset (FR-007) | ✅ (inherits `005`'s empty-segment-dropping) |
| G8 | Any number of markers, each independently effective (FR-008) | ✅ (linear pass, unbounded) |
| G9 | `page_break` adjacent to `column_reset` (either order) always resolves to a full page break (FR-009) | ✅ §3 (priority-merge, order-independent) |
| G10 | Cross-language consistency for equivalent placement (FR-010) | ✅ (pure function operating on already-resolved per-language content) |

---

## Behavioral examples

| `document.blocks` (types only) | Segments produced (`break_type`) | Pages |
|---|---|---|
| `[a, column_reset, b]` (room remains) | `[(a, None), (b, "soft")]` | 1 |
| `[a, column_reset, b]` (page already full after `a`) | `[(a, None), (b, "soft")]` | 2 — `b` overflows naturally, still left-column |
| `[a, page_break, b]` (from `005`) | `[(a, None), (b, "page")]` | 2 (unchanged from `005`) |
| `[a, page_break, column_reset, b]` | `[(a, None), (b, "page")]` | 2 — page wins |
| `[a, column_reset, page_break, b]` | `[(a, None), (b, "page")]` | 2 — page wins, order-independent |
| `[a, column_reset, column_reset, b]` | `[(a, None), (b, "soft")]` | 1 (if room) — consecutive collapse |

---

## CSS mechanism (implementation detail, documented for traceability)

```css
.sheet { column-count: 2; column-gap: 5mm; }            /* unchanged from 002/005 */
.sheet + .sheet { break-before: page; }                  /* unchanged from 005: default for
                                                              any new segment */
.sheet + .sheet.sheet--soft { break-before: auto; }       /* new: cancels the forced page
                                                              specifically for column_reset
                                                              segments */
```

One `.sheet` (or `.sheet sheet--soft`) div is rendered per non-empty `Segment`, per its resolved
`break_type`.
