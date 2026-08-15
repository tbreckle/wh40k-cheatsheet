# Implementation Plan: Page Breaks in Generated Output

**Branch**: `005-page-breaks` | **Date**: 2026-08-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/005-page-breaks/spec.md`

## Summary

Add a new `page_break` content-block kind that maintainers can insert anywhere in a document's
ordered block list (`002-pdf-generation`'s content model). The renderer partitions the block list
into segments at each `page_break` marker — **dropping any resulting empty segment** — and renders
each non-empty segment as its own top-level two-column `.sheet` container, instead of today's single
`.sheet` wrapping the entire document. A CSS adjacent-sibling rule, `.sheet + .sheet { break-before:
page }`, forces every segment after the first onto a new page. This design was chosen after an
empirical finding: WeasyPrint does **not** honor a forced `break-before: page` on an element nested
*inside* a `column-count` multicol container — it only works when the forced break is on a sibling of
a multicol container at the top level. Splitting into sibling `.sheet` segments sidesteps that
limitation entirely and, as a side effect, makes the leading/trailing/consecutive-marker edge cases
(FR-004/005/006) fall out for free: an empty segment is simply never emitted.

## Technical Context

**Language/Version**: Python 3.12+ (shared with features 001–004)

**Primary Dependencies**: None new. Uses the existing Jinja2 template engine and WeasyPrint renderer
from `002-pdf-generation`; segmentation logic is added as a small pure-Python helper registered as a
Jinja2 template global.

**Storage**: N/A — page-break markers are ordinary entries in existing `content.yaml` files (feature
002/003 convention); no new storage mechanism.

**Testing**: pytest. A pure-Python unit test for the segmentation helper (grouping/edge-case logic)
plus an integration test asserting generated PDF page counts match expectations for marker placement,
per feature 004's existing test conventions.

**Target Platform**: Same as features 001–004 — local dev + CI (Linux), WeasyPrint-rendered PDF.

**Project Type**: Single project — extends `templates/cheatsheet.html.j2` and
`src/wh40k_cheatsheet/render/html_renderer.py`; no new modules.

**Performance Goals**: Segmentation is a single linear pass over the block list; no measurable impact
on the existing <10s per-PDF generation budget (feature 002 SC-006).

**Constraints**: Must not require authors to restructure existing content — `page_break` is just one
more block type in the same ordered list (FR-010). Must not change output for documents with zero
page-break markers (backward compatible with all `002`/`003` content, including the real `11e`
content, which currently has none).

**Scale/Scope**: Touches one template file and one renderer module. No limit on the number of markers
per document (FR-007), verified empirically up to 3 segments with linear page-count scaling.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment |
|-----------|------------|
| I. Code Quality | **Satisfied.** One small, pure, independently testable helper function; no new dependencies; ships under the existing gates. |
| II. Testing Standards (NON-NEGOTIABLE) | **Satisfied by design.** Segmentation grouping logic is pure and unit-testable in isolation; page-count assertions per spec scenario map directly to an integration test. |
| III. User Experience Consistency | **Directly served.** Gives maintainers deliberate, predictable control over pagination — the spec's entire purpose — without disturbing existing layout for content that doesn't use it. |
| IV. Performance Requirements | **Satisfied.** Single linear pass; no measurable overhead. |
| Additional Constraints & Standards | **Satisfied.** No new dependencies; page-break markers are ordinary version-controlled content, same review process as any other block. |
| Development Workflow & Quality Gates | **Satisfied.** Ships through the same PR-gated workflow as prior features. |

**Verdict**: PASS. No violations; Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/005-page-breaks/
├── plan.md               # This file
├── research.md            # Phase 0 output (includes the empirical WeasyPrint findings)
├── data-model.md          # Phase 1 output
├── quickstart.md          # Phase 1 output
├── contracts/
│   └── page-break-block.md   # The page_break block contract + CSS segmentation contract
└── tasks.md                # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root) — changes to existing files

```text
templates/cheatsheet.html.j2
    # CHANGED:
    #  - existing single-block-dispatch logic extracted into a `render_block(block)` macro
    #  - the outer `{% for block in document.blocks %}` loop replaced by
    #    `{% for segment in group_by_page_breaks(document.blocks) %}` producing one
    #    `<div class="sheet">...</div>` per non-empty segment, calling `render_block` per block
    #  - new CSS rule: `.sheet + .sheet { break-before: page; }`

src/wh40k_cheatsheet/render/html_renderer.py
    # CHANGED: register `group_by_page_breaks` as a Jinja2 template global in `_environment()`
    #  - pure function: list[dict] -> list[list[dict]], splitting on {"type": "page_break"},
    #    dropping empty segments (handles start/end/consecutive-marker edge cases)

tests/
├── unit/test_page_breaks.py           # NEW: group_by_page_breaks() edge cases (start/end/consecutive/none/many)
└── integration/test_page_break_pdf.py # NEW: generated PDF page counts for marker placements
```

**Structure Decision**: No new modules or dependencies — the feature is a template restructuring
(macro extraction + segment loop + one CSS rule) plus one pure helper function exposed to the
template. This keeps the change minimal and localized to the two files that already own rendering
concerns (`html_renderer.py` for Jinja2 setup, `cheatsheet.html.j2` for layout/markup), consistent
with feature 002's module boundaries.

## Complexity Tracking

> No constitution violations. Section intentionally left empty.
