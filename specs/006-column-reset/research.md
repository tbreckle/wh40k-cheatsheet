# Phase 0 Research: Column Reset in Generated Output

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md)

This feature's central risk was whether a "soft" reset — realign to the left column without forcing
a page — is achievable at all given `005-page-breaks`'s existing `.sheet + .sheet { break-before:
page; }` rule, which would otherwise force a page on *every* new segment, including ones meant to be
soft. Resolved by direct experimentation against the installed WeasyPrint (v69.0), extending
`005`'s methodology.

---

## 1. A modifier class can override the forced-page default per segment

**Decision**: Segments produced by a `column_reset` marker render with an additional
`sheet--soft` class. One new CSS rule cancels the forced break specifically for them:

```css
.sheet + .sheet { break-before: page; }              /* 005 default: unchanged */
.sheet + .sheet.sheet--soft { break-before: auto; }   /* new: cancels it for soft resets */
```

**Verification** (empirical): a plain sibling `.sheet` (no modifier) still forces a page (2 pages,
regression-safe for `005`). A `.sheet.sheet--soft` sibling with short content following it **stays
on the same page** (1 page total) — the forced break is correctly cancelled.

```text
A) plain sibling (005 default, forces page):                2 pages  ✅ (regression-safe)
B) soft-reset sibling, short content, same page expected:    1 page  ✅
```

**Rationale**: CSS specificity — a more specific selector (`.sheet + .sheet.sheet--soft`) overrides
the less specific one (`.sheet + .sheet`) for elements matching both. This required no change to
`005`'s existing rule or its behavior for plain `page_break`-triggered segments.

**Alternatives considered**:
- *Invert the default (no-force by default, force via a modifier class instead)*: would require
  changing `005`'s existing CSS and re-verifying its entire test suite; rejected in favor of a
  strictly additive change that leaves `005`'s contract untouched.

---

## 2. "Same page when room remains, natural overflow when full" both work correctly

**Decision**: No explicit "is there room" check is needed in code — `break-before: auto` simply lets
WeasyPrint's ordinary content-flow/overflow logic decide, which is exactly the desired behavior
(spec FR-003/SC-002).

**Verification** (empirical):
- With room remaining on the page, a soft-reset segment stays on the same page (§1, Case B: 1 page).
- With the preceding segment genuinely filling multiple pages' worth of content, a soft-reset segment
  naturally overflows onto whichever page has room — confirmed via a 3-page result where the
  overflow-heavy first segment consumed pages 1–2 and the soft-reset segment landed on page 3.
- Directly inspecting the rendered layout box tree, the soft-reset content's horizontal position
  (`x ≈ 46pt`, well within the left half of an ~595pt-wide A4 page) confirms it lands in the **left
  column**, not merely "some page" — satisfying FR-002/SC-001 even after overflow.

**Rationale**: Every new `.sheet` div is its own independent multicol formatting context that always
balances its own content starting from its own column 1 — this was already established in `005`'s
research (§2) for the forced-page case, and holds identically here; only the page-timing differs
(auto vs. forced), never the column-1-first guarantee.

---

## 3. Priority-merge rule: `page_break` always wins when adjacent to `column_reset`

**Decision**: When resolving the marker(s) immediately preceding a segment, if **any** marker in that
run is `page_break`, the segment is treated as `"page"` (forces a break) — regardless of whether a
`column_reset` also appears in the same run, and regardless of order.

**Verification** (empirical), using the actual segmentation algorithm (research.md pseudocode in
data-model.md) end-to-end through real rendering:

```text
page_break then column_reset, nothing between:   2 pages  ✅ (page wins)
column_reset then page_break, nothing between:   2 pages  ✅ (page wins, order-independent)
column_reset alone, short content:               1 page   ✅ (no forced page)
```

**Rationale**: This directly implements the spec's stated resolution for the adjacency edge case
(User Story 3 / Edge Cases: "the more specific transition (the page break) determines the outcome").
"Page" is the stronger instruction (an explicit new-page request); "soft" is the weaker one (a
column realignment that yields to available space). A merge that always favors the stronger,
explicit instruction is the only reading consistent with treating `page_break` as authoritative.

**Alternatives considered**:
- *Last-marker-wins*: simpler to implement but contradicts the spec's explicit rule and would make
  output depend on marker ordering in a way authors would find surprising (page_reset, column_reset
  →  page vs column_reset, page_break → page — inconsistent "wins" logic depending on position is
  exactly what the spec's rule was written to avoid).
- *Reject documents with adjacent mixed markers as invalid*: unnecessarily strict; nothing in the
  spec calls for rejecting this, only for defining its outcome.

---

## 4. Segmentation function evolves rather than duplicates

**Decision**: `005`'s `group_by_page_breaks(blocks) -> list[list[dict]]` becomes
`group_by_breaks(blocks) -> list[Segment]`, where `Segment` carries both `blocks` and a
`break_type: Literal["page", "soft"] | None`. The single existing call site (the template) is updated
in the same change.

**Rationale**: A single linear pass must consider both marker types together to resolve the
priority-merge rule (§3) — two independent functions (one per marker type) could not correctly
express "page_break wins over an adjacent column_reset," since that requires knowing about both
marker kinds within the same boundary-resolution step. Evolving the existing function in place avoids
maintaining two near-duplicate segmentation implementations that could drift apart.

**Alternatives considered**:
- *Two-pass approach (split on page_break first, then column_reset within each part)*: this could
  work but is more complex to reason about for the adjacency edge case, and offers no benefit over a
  single pass with an accumulating "pending break type" variable (see data-model.md for the exact
  algorithm).

---

## Resolved unknowns summary

| Unknown | Resolution |
|---------|------------|
| Can a per-segment CSS override cancel the forced page break? | Yes (verified) — `.sheet + .sheet.sheet--soft { break-before: auto; }` |
| Does "same page if room, overflow if not" work without explicit logic? | Yes (verified) — `break-before: auto` + WeasyPrint's normal flow |
| Does content after a soft reset reliably land in the left column? | Yes (verified) — confirmed via direct box-position inspection, both same-page and post-overflow |
| Adjacent mixed markers (page_break + column_reset, either order) | `page_break` always wins (verified end-to-end) |
| Segmentation function design | Evolve `group_by_page_breaks` → `group_by_breaks` returning typed `Segment`s; single pass with an accumulating "pending break type" |

No open NEEDS CLARIFICATION items remain. All key risks were resolved empirically, not by
assumption, consistent with `005-page-breaks`'s methodology.
