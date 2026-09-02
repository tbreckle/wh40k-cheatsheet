# Contract: Glossary Spanning Flag

Feature: [spec.md](../spec.md) · Plan: [plan.md](../plan.md) · Data model: [data-model.md](../data-model.md)
Related: [spanning-headline-block.md](./spanning-headline-block.md)

Added 2026-08-14 (Clarifications). Extends the existing `glossary` block
(`002-pdf-generation`) with an optional flag that reuses this feature's spanning mechanism for the
glossary's own title bar.

---

## Authoring contract

Add `spanning: true` to an existing `glossary` block:

```yaml
document:
  blocks:
    - type: glossary
      title: "CORE ABILITIES"
      spanning: true          # optional; defaults to off
      terms:
        - {term: "ASSAULT", text: "..."}
        - ...
```

- `spanning` is optional and defaults to off (falsy/absent) — every glossary block that doesn't set
  it renders exactly as it did before this addition.
- Makes both the glossary's title bar and its term list span the full page width (bug fix,
  2026-08-15 — see below); the term *content* is otherwise unaffected either way.
- No other fields change meaning; `title` and `terms` behave exactly as documented in
  `002-pdf-generation`.

**2026-08-15 bug fix**: The original design (Clarifications 2026-08-14) applied spanning to the
title only, leaving the `.glossary` term-list div in normal (non-spanning) flow. That div also sets
its own `column-count: 2`. With a long enough term list (e.g. the real 36-term CORE ABILITIES
content), the non-spanning div fragments across the outer article's 2-column layout, and each
fragment independently applies its own 2 sub-columns — 4 visible narrow columns instead of 2. Fixed
by applying `column-span: all` to the `.glossary` div itself (via a `glossary--spanning` modifier
class) whenever `spanning: true`, so the whole block — title and term list — renders as one
full-width, cleanly 2-column unit. Reported directly against the real `11e` English/German output.

---

## Rendering contract

| # | Guarantee | Basis |
|---|-----------|-------|
| G1 | `spanning: true` makes the glossary's title span both columns, identically to a standalone `spanning_headline` (FR-011) | Reuses `.phase--spanning`, verified in `spanning-headline-block.md` G1 |
| G2 | `spanning: true` also makes the glossary's term-list div span both columns as one full-width, 2-column block — not fragmented into 4 narrow columns | The `.glossary` div is wrapped in a `.block--full-width` (`column-span: all`) element (2026-08-15 fix; re-implemented 2026-09-02, see below); verified against real 36-term CORE ABILITIES content in both `en`/`de` |
| G3 | The glossary's term *content* (text, order, count) is identical whether `spanning` is set or not — only the wrapping div's class differs | `tests/integration/test_glossary_spanning_pdf.py::test_glossary_term_list_content_identical_regardless_of_spanning_flag` |
| G4 | Omitting `spanning` (or setting it falsy) preserves the exact pre-existing glossary rendering — no regression for content authored before this addition | Conditional class application only; no change to the default path |
| G5 | Coexists correctly with `page_break`/`column_reset`, exactly as the glossary block already does | The glossary block is dispatched the same way regardless of `spanning`; no new interaction surface |

**2026-09-02 layout-crash fix**: applying `column-span: all` to the `.glossary` div *itself* was
found to crash WeasyPrint (69.0). An element that is simultaneously a multi-column container
(`.glossary` sets `column-count: 2`) and a spanner of its parent's columns trips an internal layout
assertion — a bare `AssertionError` from `assert not page_is_empty` (`weasyprint/layout/page.py`) —
whenever that block lands at a page boundary. It surfaced on real `11e` German content once enough
text accumulated ahead of the CORE ABILITIES glossary, and was independent of any single
paragraph's wording or length: replacing the block before it with *any* other block type still
crashed, while moving it elsewhere did not. Sweeping filler amounts, 28 of 66 layout combinations
crashed.

Fixed by splitting the two roles across two elements — the `.glossary` div keeps `column-count: 2`
and is wrapped, when `spanning: true`, in a `.block--full-width` element (the same
`column-span: all` rule feature 009 already uses for full-width lists). Rendered output is
unchanged: the wrapper, the inner `.glossary`, and its two balanced sub-columns measure 748.3pt /
748.3pt / 364.7pt each, exactly as before. The `glossary--spanning` class and its CSS rule are
retired, since the wrapper now carries the spanning role. Regression-tested by
`tests/integration/test_glossary_spanning_pdf.py::test_spanning_glossary_at_a_page_boundary_does_not_crash_layout`,
which sweeps the glossary across a page boundary and fails on the pre-fix template.

---

## CSS mechanism (implementation detail, documented for traceability)

The existing glossary title markup gains a conditional class, same as before:

```text
<h2 class="phase{{ ' phase--spanning' if block.spanning | default(false) else '' }}">{{ block.title }}</h2>
```

`.phase--spanning { column-span: all; }` (defined once, in `spanning-headline-block.md`'s CSS
mechanism section) applies verbatim.

As of the 2026-09-02 fix, the glossary's own `<div>` is wrapped, rather than classed, when spanning:

```text
{%- if glossary_spanning %}<div class="block--full-width">{% endif %}
<div class="glossary">
  ...terms...
</div>
{%- if glossary_spanning %}</div>{% endif %}
```

```css
.block--full-width {
  column-span: all;   /* shared with feature 009's full-width lists */
}
```

The spanning role (`column-span: all`, on the wrapper) and the two-column role
(`column-count: 2`, on `.glossary`) must stay on **separate elements** — combining them on one
element is what crashed WeasyPrint's layout engine. `.glossary--spanning` no longer exists.

(`| default(false)`, captured once into `glossary_spanning`, guards against `StrictUndefined` when
the optional `spanning` key is absent, on both the title and the wrapper.)
