# Implementation Plan: Full-Width Spanning Headline

**Branch**: `007-spanning-headline` | **Date**: 2026-08-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/007-spanning-headline/spec.md`

## Summary

Add a new `spanning_headline` content block — a visible heading block (carries its own `title`, like
the existing `phase` block) that renders using CSS `column-span: all`, causing its background and
text to stretch across the complete width of the two-column layout at its position. This is
architecturally simple and low-risk: `column-span` operates entirely *within* a single `.sheet`
container's own multi-column formatting context, so it is completely orthogonal to `005-page-breaks`
and `006-column-reset`'s segment-splitting mechanism (which decides which `.sheet` a block belongs
to, not how content renders within one). The spanning headline is therefore just one more branch in
the existing `render_block` macro's dispatch chain — no changes are needed to `group_by_breaks()`,
the segmentation algorithm, or either prior feature's behavior. The mechanism was verified end-to-end
against the installed WeasyPrint (visually rendered and inspected) before committing to this design.

**2026-08-14 addition** (per Clarifications): the existing `glossary` block (`002-pdf-generation`)
gains an optional `spanning` flag that applies the *same* `phase--spanning` CSS class, already shipped
by this feature, to the glossary's own title bar only — its term-list layout is untouched. This
requires no new CSS and no new research; it is a one-line conditional class addition to the existing
`glossary` dispatch branch, reusing the exact mechanism verified in research.md §1.

**2026-08-15 fix**: title-bar-only spanning turned out to be a latent bug — a non-spanning
`.glossary` div long enough to overflow one outer column (the real 36-term CORE ABILITIES content)
fragments across the outer 2-column layout, and each fragment applies the glossary's own
`column-count: 2` independently, producing 4 visible columns instead of 2. Fixed by adding a second
`glossary--spanning { column-span: all; }` class, applied to the `.glossary` div itself alongside the
title's existing `phase--spanning` class, whenever `spanning: true`. One more conditional class,
same mechanism, no new CSS concept.

## Technical Context

**Language/Version**: Python 3.12+ (shared with features 001–006)

**Primary Dependencies**: None new — pure CSS/template addition on the existing Jinja2/WeasyPrint
stack from `002-pdf-generation`.

**Storage**: N/A — a spanning headline is an ordinary entry in existing `content.yaml` files, using
the same `document.blocks` convention as every other block type.

**Testing**: pytest. Integration tests asserting the rendered box width of a spanning headline
approximates the full content width (vs. a standard heading's single-column width), that surrounding
content is unaffected, and that it coexists correctly with `page_break`/`column_reset` markers —
following the box-inspection methodology established in `006-column-reset`.

**Target Platform**: Same as features 001–006 — local dev + CI (Linux), WeasyPrint-rendered PDF.

**Project Type**: Single project — extends `templates/cheatsheet.html.j2` only. No changes to any
Python module; this is a template-and-CSS-only feature.

**Performance Goals**: `column-span` is a standard, cheap CSS layout feature; no measurable impact on
the existing <10s per-PDF generation budget.

**Constraints**: Must not alter rendering for any existing block type or any document that doesn't
use the new block (backward compatible with all `002`/`003`/`005`/`006` content, including the real
`11e` content). Must remain visually distinct from the existing single-column `phase` heading
(FR-003) — reuses the same green-bar visual language but at full width, which is inherently
distinguishable purely by its width/position, satisfying the distinguishability requirement without
needing a different color.

**Scale/Scope**: One new block type, one new CSS rule, one new macro branch. No limit on how many
spanning headlines a document may contain (FR-006). Plus one optional boolean field (`spanning`) on
the existing `glossary` block, reusing the same CSS class (FR-011) — no new CSS rule for this part.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment |
|-----------|------------|
| I. Code Quality | **Satisfied.** Minimal, template-only addition; one new CSS rule; no new Python code at all. Ships under the existing gates. |
| II. Testing Standards (NON-NEGOTIABLE) | **Satisfied by design.** Box-width/position assertions map directly to FR-002/FR-003; coexistence tests with `005`/`006` markers are straightforward given the orthogonal architecture. |
| III. User Experience Consistency | **Directly served.** Gives maintainers a genuinely distinct, full-width visual break — the entire purpose of the feature — using the same visual language (green bar) as existing headings for consistency. |
| IV. Performance Requirements | **Satisfied.** `column-span` is a standard, inexpensive CSS feature; no measurable overhead. |
| Additional Constraints & Standards | **Satisfied.** No new dependencies; content stays version-controlled and structure-only where applicable. |
| Development Workflow & Quality Gates | **Satisfied.** Ships through the same PR-gated workflow as prior features. |

**Verdict**: PASS. No violations; Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/007-spanning-headline/
├── plan.md               # This file
├── research.md            # Phase 0 output (empirical column-span verification)
├── data-model.md          # Phase 1 output
├── quickstart.md          # Phase 1 output
├── contracts/
│   ├── spanning-headline-block.md   # The spanning_headline block contract
│   └── glossary-spanning-flag.md    # [2026-08-14] The glossary spanning flag contract
└── tasks.md                 # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root) — changes to existing files

```text
templates/cheatsheet.html.j2
    # CHANGED (only file touched):
    #  - new branch in the `render_block` macro's dispatch chain for
    #    `type == 'spanning_headline'`, rendering `<h2 class="phase phase--spanning">{{ title }}</h2>`
    #  - new CSS rule: `.phase--spanning { column-span: all; }` (reuses existing `.phase`
    #    styling for color/typography; column-span is the only new visual behavior)
    #  - header doc comment documents the new `spanning_headline` block type
    #  - [2026-08-14 addition] the existing `glossary` branch's `<h2 class="phase">` gains a
    #    conditional `phase--spanning` class when `block.spanning` is truthy — reuses the CSS
    #    rule above verbatim; the glossary's `<div class="glossary">` term list is untouched

tests/
├── integration/test_spanning_headline_pdf.py   # box-width assertions, surrounding-content
│                                                 # integrity, coexistence with page_break/column_reset
└── integration/test_glossary_spanning_pdf.py   # NEW [2026-08-14]: glossary title spans when
                                                   # `spanning: true`; term list layout unchanged;
                                                   # defaults to off (existing content unaffected)
```

**Structure Decision**: A single-file change to `templates/cheatsheet.html.j2` — no Python code is
touched at all, since `column-span` is purely a CSS/rendering concern that composes with the existing
`render_block` macro exactly like every other block type. This is the leanest possible design for
this feature, consistent with `005`/`006`'s pattern of keeping new capabilities additive and
low-risk.

## Complexity Tracking

> No constitution violations. Section intentionally left empty.
