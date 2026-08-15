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
| G2 | `spanning: true` also makes the glossary's term-list div span both columns as one full-width, 2-column block — not fragmented into 4 narrow columns | `glossary--spanning { column-span: all; }` applied to the `.glossary` div itself (2026-08-15 fix); verified against real 36-term CORE ABILITIES content in both `en`/`de` |
| G3 | The glossary's term *content* (text, order, count) is identical whether `spanning` is set or not — only the wrapping div's class differs | `tests/integration/test_glossary_spanning_pdf.py::test_glossary_term_list_content_identical_regardless_of_spanning_flag` |
| G4 | Omitting `spanning` (or setting it falsy) preserves the exact pre-existing glossary rendering — no regression for content authored before this addition | Conditional class application only; no change to the default path |
| G5 | Coexists correctly with `page_break`/`column_reset`, exactly as the glossary block already does | The glossary block is dispatched the same way regardless of `spanning`; no new interaction surface |

---

## CSS mechanism (implementation detail, documented for traceability)

The existing glossary title markup gains a conditional class, same as before:

```text
<h2 class="phase{{ ' phase--spanning' if block.spanning | default(false) else '' }}">{{ block.title }}</h2>
```

`.phase--spanning { column-span: all; }` (defined once, in `spanning-headline-block.md`'s CSS
mechanism section) applies verbatim.

As of the 2026-08-15 fix, the glossary's own `<div>` gains the same conditional treatment:

```text
<div class="glossary{{ ' glossary--spanning' if block.spanning | default(false) else '' }}">
```

```css
.glossary--spanning {
  column-span: all;
}
```

(`| default(false)` guards against `StrictUndefined` when the optional `spanning` key is absent, on
both elements.)
