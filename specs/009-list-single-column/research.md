# Phase 0 Research: List Single-Column (Full-Width) Flag

Feature: [spec.md](./spec.md)

The spec's Clarification already resolved *what* "single column" means (full page width, not a
narrower confinement). This research verifies the *mechanism* against the actually-installed
WeasyPrint, using the real `templates/cheatsheet.html.j2` file and real `@page` A4 sizing — following
this project's established discipline (used for `005`–`008`) of empirically confirming CSS behavior
before committing to a design, rather than assuming it from the spec alone.

---

## 1. Does `column-span: all` work on a `list` block's wrapper the same way it works on a heading?

**Decision**: Yes — reuse the exact `column-span: all` mechanism already shipped for
`spanning_headline` (`007-spanning-headline`) and the glossary's `spanning` flag, applied to the
`list` block's existing `<div class="block">` wrapper via a new `.block--full-width` CSS class.

**Rationale**: Verified empirically by patching a scratch copy of the real template (conditional
class on the `list` branch's wrapper `div`, plus `.block--full-width { column-span: all; }` in the
real `<style>` block) and rendering a real fixture through the actual `render_html` pipeline function
and WeasyPrint — not a synthetic HTML scaffold, so the real `@page` A4 sizing and real
`.sheet { column-count: 2 }` context apply exactly as they will in production. Measured via
box-width inspection (same methodology as `007`'s research):

| Element | Rendered width | Interpretation |
|---|---|---|
| Standard paragraph (before) | ≈364.7pt | One column's width |
| Standard list (no flag) | ≈351.4pt | Confined to one column, as today |
| Flagged list | ≈735.0pt | ≈2× a single column's width — full page width |
| Standard paragraph (after) | ≈364.7pt | Unaffected, matches the "before" paragraph exactly |

Content order was also confirmed preserved (`FULLWIDTHITEM` before `ENDMARKER` before
`STANDARDITEM` in the rendered HTML, matching document order) — surrounding content is not
reordered, lost, or duplicated.

**A note on synthetic-HTML pitfalls**: an initial attempt at this verification used a hand-rolled
HTML scaffold (a `.sheet` with an explicit `width: 400pt`, no real `@page`) and got an
unexplained/inconsistent width reading (627pt against a 400pt container). Switching to the real
template + real pipeline + real A4 `@page` context (matching how `005`–`008` all did their CSS
verification) resolved the discrepancy and produced numbers that make sense. **Lesson carried
forward**: verify CSS mechanisms against the real template file, not a simplified reconstruction —
simplified scaffolds can silently diverge from the real page-sizing context and produce misleading
results.

**Alternatives considered**:
- *A dedicated new CSS mechanism instead of reusing `column-span: all`*: rejected — would duplicate
  a mechanism already proven correct twice (`007`, and its `008`-adjacent glossary extension),
  for no behavioral difference. Reuse is also what FR-005 asks for (visual consistency with existing
  full-width elements).

---

## 2. Schema key naming

**Decision**: `single_column: true` on the `list` block (optional, default falsy/absent).

**Rationale**: The spec's own resolved language is "single column" (not "spanning") — content
authors think of this list as "the one that gets to use the whole width," and `single_column`
reads naturally in that context without requiring authors to know the internal CSS term. This
mirrors the existing convention of per-block-type boolean flags named for what an author is asking
for (`glossary.spanning`, `callout.variant`), not for the underlying mechanism.

**Alternatives considered**:
- *`spanning: true`, matching `glossary.spanning` exactly*: rejected — would be internally
  consistent with the CSS term, but the spec explicitly settled on "single column" as the
  user-facing concept for lists specifically, and `spanning` on a `list` block could be misread as
  "this list itself spans/scrolls further," which isn't what it does.

---

## 3. Interaction with `page_break`/`column_reset` and nested sub-items

**Decision**: No special handling needed — same orthogonal-architecture conclusion as `007`/`008`.

**Rationale**: `column-span: all` operates entirely within a single `.sheet`'s own multi-column
formatting context; it has no interaction with `group_by_breaks()`'s segmentation, which decides
which `.sheet` a block belongs to, not how content renders within one (confirmed in
`007-spanning-headline/research.md` §2 and unchanged since). A flagged list's nested `sub` items
render via the same `render_list` macro as today — the flag only changes the wrapping `<div>`'s
class, nothing about `render_list`'s own markup — so sub-item indentation/bullet styling is
untouched by construction, not by a new rule needing verification.

---

## Resolved unknowns summary

| Unknown | Resolution |
|---------|------------|
| Does `column-span: all` work on a list's wrapper div, not just headings? | Yes — verified empirically against the real template; ≈735pt (full width) vs. ≈351–365pt (single column) |
| Schema key name | `single_column: true` on the `list` block, optional, default off |
| Interaction with `page_break`/`column_reset` | None needed — orthogonal, per `007`'s already-proven architecture |
| Nested sub-item rendering under the flag | Unaffected — `render_list`'s own markup is untouched, only the wrapper `div`'s class changes |

No open NEEDS CLARIFICATION items remain.
