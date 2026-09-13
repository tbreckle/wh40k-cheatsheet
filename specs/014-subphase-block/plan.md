# Implementation Plan: Subphase Heading

**Branch**: `014-subphase-block` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/014-subphase-block/spec.md`

## Summary

Add a new `subphase` content block — a visible heading block (carries its own `title`, like the
existing `phase` block) that reuses `phase`'s exact markup shape (`<h2 class="phase ...">`) plus one
modifier class, `phase--sub`, which overrides only `background-color` to a slightly brighter shade of
the same green used by `phase`. This is architecturally identical to `007-spanning-headline`'s
`spanning_headline` (a new heading block that reuses `.phase` styling and adds one modifier class) —
the only difference is which CSS property the modifier changes (`background-color` here, vs.
`column-span` there). No changes are needed to `group_by_breaks()`, the segmentation algorithm, or any
prior feature's behavior: `subphase` is just one more branch in the existing `render_block` macro's
dispatch chain, and one more `:root` custom property alongside the existing `--green-dark`/
`--green-sub`/`--green-very-light` palette, following `011-print-friendly-pdf`'s established pattern
of a light-mode/grayscale pair per custom property.

## Technical Context

**Language/Version**: Python 3.12+ (shared with prior features)

**Primary Dependencies**: None new — pure CSS/template addition on the existing Jinja2/WeasyPrint
stack from `002-pdf-generation`.

**Storage**: N/A — a `subphase` heading is an ordinary entry in existing `content.yaml` files, using
the same `document.blocks` convention as every other block type.

**Testing**: pytest. Integration tests asserting the rendered background color of a `subphase`
heading is brighter (higher luminance) than a `phase` heading's, at the same width/position; that it
coexists correctly with `page_break`/`column_reset`; that it remains distinguishable from `phase` in
print-friendly grayscale mode (extending `011-print-friendly-pdf`'s existing color-distinguishability
test suite); and that it renders consistently across languages — following the box-inspection
methodology established in `006-column-reset`/`007-spanning-headline` and the color-inspection
methodology established in `011-print-friendly-pdf`.

**Target Platform**: Same as prior features — local dev + CI (Linux), WeasyPrint-rendered PDF.

**Project Type**: Single project — extends `templates/cheatsheet.html.j2` only. No changes to any
Python module; this is a template-and-CSS-only feature.

**Performance Goals**: A new CSS custom property and one modifier class are negligible; no measurable
impact on the existing <10s per-PDF generation budget.

**Constraints**: Must not alter rendering for any existing block type or any document that doesn't
use the new block (backward compatible with all prior content, including the real `11e` content).
Must remain visually distinct from both `phase` (brighter background, same width) and `subsection`
(a different, pre-existing lighter-green heading level used for a different kind of grouping — see
research.md §2) and from `spanning_headline` (distinguished by width, not color). Must resolve to a
distinct grayscale shade from `phase` in print-friendly mode (FR-004).

**Scale/Scope**: One new block type, one new CSS custom property (with its print-friendly grayscale
pair), one new CSS rule, one new macro branch. No limit on how many `subphase` headings a document
may contain (FR-005).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment |
|-----------|------------|
| I. Code Quality | **Satisfied.** Minimal, template-only addition; one new CSS custom property/rule; no new Python code at all. Ships under the existing gates. |
| II. Testing Standards (NON-NEGOTIABLE) | **Satisfied by design.** Color/luminance assertions map directly to FR-003/FR-004; coexistence tests with `005`/`006` markers and cross-language tests follow the already-established patterns from `007`/`011`. |
| III. User Experience Consistency | **Directly served.** Gives maintainers a genuinely distinct nested-heading level using the same visual language (green bar) as `phase`, for consistency, while remaining clearly distinguishable. |
| IV. Performance Requirements | **Satisfied.** A CSS custom property and one modifier class are negligible; no measurable overhead. |
| Additional Constraints & Standards | **Satisfied.** No new dependencies; content stays version-controlled and structure-only where applicable. |
| Development Workflow & Quality Gates | **Satisfied.** Ships through the same PR-gated workflow as prior features. |

**Verdict**: PASS. No violations; Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/014-subphase-block/
├── plan.md                          # This file
├── research.md                      # Phase 0 output
├── data-model.md                    # Phase 1 output
├── quickstart.md                    # Phase 1 output
├── contracts/
│   └── subphase-block.md            # The subphase block contract
└── tasks.md                         # Phase 2 (/speckit-tasks)
```

### Source Code (repository root) — changes to existing files

```text
templates/cheatsheet.html.j2
    # CHANGED (only file touched):
    #  - new branch in the `render_block` macro's dispatch chain for
    #    `type == 'subphase'`, rendering `<h2 class="phase phase--sub">{{ title }}</h2>`
    #  - new `:root` custom property `--green-subphase` (light-mode/grayscale pair, following the
    #    existing `--green-dark`/`--green-sub` pattern from `011-print-friendly-pdf`)
    #  - new CSS rule: `.phase--sub { background: var(--green-subphase); }` (reuses existing
    #    `.phase` styling for typography/padding/width; the background override is the only new
    #    visual behavior)
    #  - header doc comment documents the new `subphase` block type

docs/CONTENT_AUTHORING.md
    # CHANGED: new section documenting `{type: subphase}`, mirroring the existing
    #  `spanning_headline` section

tests/
├── integration/test_subphase_pdf.py             # NEW: brighter-background assertion, same-width
│                                                   assertion, surrounding-content integrity,
│                                                   coexistence with page_break/column_reset
├── integration/test_subphase_cross_language.py  # NEW: equivalent placement renders the identical
│                                                   background color across languages
└── integration/test_print_friendly_pdf.py       # CHANGED: `subphase` added to the all-variants
                                                    fixture; new test asserting `phase`/`subphase`
                                                    remain distinguishable in grayscale mode
```

**Structure Decision**: A single-file change to `templates/cheatsheet.html.j2`, plus documentation and
test-only additions — no Python code is touched at all, exactly like `007-spanning-headline`. This is
the leanest possible design for this feature.

## Complexity Tracking

> No constitution violations. Section intentionally left empty.
