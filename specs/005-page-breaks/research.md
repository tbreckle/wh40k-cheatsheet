# Phase 0 Research: Page Breaks in Generated Output

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md)

The central technical risk was whether WeasyPrint (the existing PDF renderer from
`002-pdf-generation`) honors a forced page break placed *inside* the template's
`column-count: 2` multi-column layout. This was resolved by direct experimentation against the
installed WeasyPrint (v69.0) rather than assumption, since it determines the entire design.

---

## 1. Forced breaks do not propagate out of a CSS multicol container

**Finding** (empirical, `.venv/bin/python` + `weasyprint`): a `break-before: page` (or the legacy
`page-break-before: always`) declared on an element that is a descendant of a `column-count`
container is **silently ignored** — the document still renders as a single page. The same rule on
the same markup, *outside* any multicol container, works correctly (produces 2 pages for a
before/after split).

```text
simple break-before page (no multicol):        2 pages   ✅ works
simple empty-div break-before (no multicol):    2 pages   ✅ works
multicol, break-before page on inner <p>:       1 page    ❌ ignored
```

**Rationale for treating this as authoritative**: this is a known category of interaction in CSS
Fragmentation implementations — multicol "balances" content across columns before fragmentation
decisions are finalized, and WeasyPrint's implementation does not currently propagate a forced
in-flow break out through an active column-balancing context to the page level. Confirming this
empirically (rather than guessing) avoided designing around a mechanism that would have silently
failed for every real generation.

**Alternatives considered**:
- *Trust the CSS Fragmentation spec's "always forces a page break regardless of context" wording*:
  rejected after the experiment contradicted it for this renderer/version — spec compliance is not
  guaranteed across all engines, and shipping on an unverified assumption would have produced a
  feature that silently does nothing.

---

## 2. Decision: segment the document into sibling `.sheet` containers

**Decision**: Partition the document's ordered block list into segments at each `page_break` marker
block. Render each segment as its **own top-level `<div class="sheet">`** (the same two-column
container used today, just one per segment instead of one for the whole document). Add exactly one
new CSS rule: `.sheet + .sheet { break-before: page; }` — an adjacent-sibling selector that forces a
page break before every `.sheet` that follows another `.sheet`, i.e. before every segment after the
first.

**Verification** (empirical): this pattern was tested directly and confirmed correct:

```text
two sibling .sheet segments:            2 pages   ✅
three sibling .sheet segments:          3 pages   ✅
```

**Rationale**: Because the forced break now sits on a top-level sibling relationship *between* two
separate multicol containers — not nested inside one — it is no longer subject to the limitation in
§1. This is architecturally simple (one CSS rule, no per-element break properties needed) and reuses
the exact column-flow styling the document already has, per segment.

**Alternatives considered**:
- *`break-after: page` on the last element of the preceding segment*: works in principle but is
  fragile — the "last element" varies per document and per language, and still requires splitting
  into separate top-level containers to have any effect (per §1), so it offers no advantage over the
  simpler adjacent-sibling rule.
- *CSS `column-span: all` trick*: spans a full-width element across both columns but does not force
  a *page* break; irrelevant to this problem.
- *Manual multi-page HTML documents with client-side concatenation*: far more complex than a template
  change; rejected.

---

## 3. Edge cases (start / end / consecutive markers) fall out of "drop empty segments"

**Decision**: The segmentation function drops any segment that contains zero blocks. A marker at the
very start produces a leading empty segment → dropped → no blank leading page (FR-004). A marker at
the very end produces a trailing empty segment → dropped → no blank trailing page (FR-005).
Consecutive markers with nothing between them produce an empty *middle* segment → dropped → only one
real page transition remains between the surrounding content (FR-006).

**Verification** (empirical): confirmed directly —

```text
break-at-start  (1 non-empty segment only): 1 page, no leading blank page   ✅
break-at-end    (1 non-empty segment only): 1 page, no trailing blank page  ✅
consecutive-breaks collapsed to 1 boundary (2 non-empty segments):  2 pages ✅
```

**Rationale**: This means the edge-case requirements need **no special-case code** — they are a
direct consequence of "don't render empty segments," which is also the simplest, most obviously
correct behavior for a segmentation function. One function, one rule, three requirements satisfied.

**Alternatives considered**:
- *Explicitly detect start/end/consecutive markers and special-case them*: unnecessary — the
  general "drop empty groups" rule already covers every case; adding special cases would be
  needless complexity contradicting the constitution's simplicity expectations.

---

## 4. Page-footer counters remain correct across segments

**Finding** (empirical): the existing `@page { @bottom-right { content: "Page " counter(page) " / "
counter(pages) } }` footer (already in `templates/cheatsheet.html.j2` from feature 002) continues to
report correct running/total page numbers (`Page 1 / 3`, `Page 2 / 3`, `Page 3 / 3`) across multiple
sibling `.sheet` segments — confirmed by rendering a 3-segment document and extracting the footer
text from the resulting PDF.

**Rationale**: `@page` counters are a page-box-level CSS Paged Media feature, orthogonal to how many
top-level flow containers exist in the body; no special handling is needed. Documented here so the
implementation phase doesn't need to re-derive this.

---

## 5. Where segmentation logic lives

**Decision**: A small pure function, `group_by_page_breaks(blocks: list[dict]) -> list[list[dict]]`,
is registered as a **Jinja2 template global** in `render/html_renderer.py`'s environment setup (the
module that already owns Jinja2 `Environment` configuration per feature 002). The template calls it
directly: `{% for segment in group_by_page_breaks(document.blocks) %}`.

**Rationale**: Keeps the function pure and independently unit-testable (no HTML/Jinja2 needed to test
grouping logic) while keeping domain knowledge of "how blocks become segments" colocated with the
renderer that already understands the block-dispatch model, rather than leaking it into
`content/resolver.py` (which only knows about file resolution, not rendering structure) or
`pipeline.py` (which orchestrates but doesn't otherwise know rendering internals).

**Alternatives considered**:
- *Precompute segments in Python before calling `render_html()`*: would require `pipeline.py` or the
  resolver to understand the block/segment domain, coupling unrelated modules; rejected in favor of
  keeping this a renderer-internal concern.
- *A custom Jinja2 filter instead of a global*: equivalent either way; `global` reads more naturally
  for a function that takes the full block list as an argument rather than transforming a piped
  value.

---

## 6. Block-type naming and existing block-dispatch refactor

**Decision**: New block type name: `page_break` (matches the existing `snake_case`-free but
consistent naming already used: `phase`, `subsection`, `paragraph`, `callout`, `table`, `keyvals`,
`glossary`, `stratagem`). The existing single per-block `{% if/elif %}` dispatch chain inside the
`{% for block in document.blocks %}` loop is extracted into a `{% macro render_block(block) %}` so it
can be invoked once per block from within the new nested segment loop without duplicating the
dispatch logic.

**Rationale**: A macro extraction is the minimal-diff way to introduce the segment loop without
rewriting every existing block-type branch; behavior for all existing block types (phase, subsection,
paragraph, list, callout, table, keyvals, glossary, stratagem) is unchanged — only the outer loop
structure changes.

**Alternatives considered**:
- *Duplicate the dispatch logic per segment*: rejected — violates DRY and risks the two copies
  drifting apart.

---

## Resolved unknowns summary

| Unknown | Resolution |
|---------|------------|
| Does forced break work inside multicol? | No (verified) — must break *between* sibling multicol containers instead |
| Segmentation mechanism | Split `document.blocks` on `page_break` markers, drop empty segments |
| CSS mechanism | `.sheet + .sheet { break-before: page; }` (verified working) |
| Start/end/consecutive edge cases | Free consequence of dropping empty segments (verified) |
| Footer page counters | Unaffected — verified correct across 3 segments |
| Where segmentation logic lives | `group_by_page_breaks()` as a Jinja2 global in `html_renderer.py` |
| Block-type name | `page_break`, dispatched via an extracted `render_block` macro |

No open NEEDS CLARIFICATION items remain. All key risks were resolved empirically, not by
assumption.
