# Phase 0 Research: Full-Width Spanning Headline

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md)

The central technical question was whether CSS `column-span: all` — the natural mechanism for
spanning an element across a `column-count: 2` container's columns — is correctly supported by
WeasyPrint, and whether it interacts safely with `005-page-breaks`/`006-column-reset`'s existing
segment-splitting mechanism. Verified empirically against the installed WeasyPrint (v69.0), per this
project's established methodology (`005`/`006` both found real, non-obvious rendering behavior only
through direct experimentation).

---

## 1. `column-span: all` works correctly in WeasyPrint

**Decision**: Use `column-span: all` on the spanning headline element.

**Verification** (empirical, both structural and visual):
- Box-tree inspection: the spanning element's outer block box measured `width ≈ 691pt` against a
  ~718pt page box — i.e., essentially the full content width — versus surrounding paragraph text
  confined to a single ~262pt-wide column.
- Direct visual rendering (PDF read back and inspected): "before" content correctly fills the left
  then right column; the spanning headline renders as one continuous full-width band cutting cleanly
  across both columns; "after" content resumes in a fresh two-column flow beneath it.

```text
"before" text 1/2:  left column   (x ≈ 46pt)
"before" text 3:     right column  (x ≈ 406pt)
spanning headline:   full width    (outer box width ≈ 691pt, spans both columns)
"after" text 1:       left column   (resumes fresh below the span)
"after" text 2:       right column
```

**Rationale**: This is exactly the "clear cut and separation on both columns" behavior the spec
requires (FR-002, SC-001) — confirmed directly rather than assumed, avoiding a repeat of `006`'s
costly detour where an incorrect assumption (not an actual bug) triggered a lengthy investigation.

**Alternatives considered**:
- *Render the headline as two half-width elements, one per column*: would not produce one continuous
  visual band or a true "background spans both columns" effect: rejected, doesn't match the spec's
  explicit ask.
- *Break out of the `.sheet` multicol container entirely and use a full-width sibling element*: this
  is architecturally closer to `005`/`006`'s segment-splitting approach, but forces a column/segment
  break at that point, which is unnecessary — `column-span: all` achieves the same visual effect
  *without* needing to interrupt document flow into separate `.sheet` segments, and it composes
  cleanly with content before/after without any special-casing.

---

## 2. Orthogonal to `005-page-breaks` / `006-column-reset`

**Decision**: No changes to `group_by_breaks()`, `Segment`, or the segment-splitting algorithm. The
spanning headline is dispatched purely within `render_block` like every other visible block type
(`phase`, `subsection`, `paragraph`, etc.) — it never participates in segmentation.

**Rationale**: `page_break` and `column_reset` are *invisible structural markers* consumed during
segmentation (deciding which `.sheet` a run of blocks belongs to); `column-span: all` is a rendering
property applied to one *visible* block once it's already inside a `.sheet`. These operate at
different layers and don't need to know about each other. A spanning headline can appear inside any
segment (page-forced, soft-reset, or the default first segment) and will span that segment's own two
columns identically, since each `.sheet` is its own independent multicol formatting context — a fact
already established in `005`'s and `006`'s research.

**Verification approach for implementation**: rather than needing new empirical CSS research for the
combination, this is confirmed by construction — a spanning headline block inside any segment's
`blocks` list is rendered by the same `render_block` call used for every other block in that segment,
inside that segment's own `.sheet`/`.sheet--soft` div, which already independently starts its own
2-column context (established in `005` research.md §2, `006` research.md §1–2). Task-phase tests
confirm this holds in practice.

---

## 3. Visual distinguishability from the standard heading

**Decision**: Reuse the existing `.phase` heading's color, typography, and padding; add only
`column-span: all` via a modifier class `.phase--spanning`. Distinguishability (FR-003/SC-004) comes
from the width/position difference itself (full-width vs. single-column), not from a different color
or style — a reader immediately sees the difference in shape without needing a legend.

**Rationale**: Keeps the two heading styles visually related (both are clearly "section headings" in
the same visual language) while making the spanning one unmistakably different in a way inherent to
its purpose, rather than relying on an arbitrary color/style distinction that a reader would need to
learn.

**Alternatives considered**:
- *A distinct color for the spanning variant*: adds a new visual language readers must learn;
  rejected as unnecessary — width alone is definitionally distinguishing.

---

## 4. Glossary spanning flag (2026-08-14 addition) — no new research required

**Decision**: Add an optional `spanning` field to the existing `glossary` block. When truthy, the
glossary's title `<h2 class="phase">` gains the same `phase--spanning` class introduced in §1. No new
CSS rule, no new empirical verification.

**Rationale**: The `glossary` block already renders its title via the identical `<h2 class="phase">`
markup pattern as the standalone `phase`/`spanning_headline` blocks (see the existing template's
`glossary` branch). Since `.phase--spanning { column-span: all; }` was already verified structurally
and visually in §1 against exactly this markup shape, applying it conditionally to the glossary's
title is a direct reuse, not a new mechanism — there is nothing new to verify. The glossary's own
`<div class="glossary">` term list (with its own independent `column-count: 2`) is a sibling element,
untouched by the title's class change, so the title-bar-only scope decided in Clarifications requires
no additional CSS scoping work either.

**Alternatives considered**:
- *Give the glossary its own dedicated CSS class (e.g., `.glossary-title--spanning`)*: functionally
  identical output, but duplicates a rule that already exists; rejected in favor of reusing
  `phase--spanning` directly, keeping one CSS rule as the single source of truth for "what spanning
  means" across every block type that offers it.

---

## Resolved unknowns summary

| Unknown | Resolution |
|---------|------------|
| Does `column-span: all` work in WeasyPrint? | Yes (verified structurally and visually) |
| Interaction with `005`/`006` segmentation | None needed — orthogonal by construction, confirmed by prior research |
| Visual distinguishability mechanism | Width/position difference alone (full-width vs. single-column), same color/typography |
| Python code changes needed | None — template/CSS only |
| Glossary spanning flag CSS mechanism | Reuses `.phase--spanning` verbatim — no new CSS, no new verification needed (§4) |

No open NEEDS CLARIFICATION items remain. The core risk was resolved empirically before committing
to the design, consistent with `005`/`006`'s methodology.
