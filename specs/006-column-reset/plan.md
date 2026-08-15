# Implementation Plan: Column Reset in Generated Output

**Branch**: `006-column-reset` | **Date**: 2026-08-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/006-column-reset/spec.md`

## Summary

Add a `column_reset` content block — a lighter-weight sibling to `005-page-breaks`'s `page_break`
marker — that forces the following content to begin in the left column of the two-column layout
**without** forcing a new page unless the current page genuinely has no room left. This requires
generalizing `005-page-breaks`'s segmentation mechanism (`group_by_page_breaks`) into a
type-aware version (`group_by_breaks`) that tracks, per segment, which kind of marker (if any)
preceded it, and a small CSS addition — a modifier class `.sheet--soft` whose
`.sheet + .sheet.sheet--soft { break-before: auto; }` rule overrides `005`'s default
`.sheet + .sheet { break-before: page; }` specifically for column-reset-triggered segments. Where
two marker types are adjacent with nothing between them, `page_break` always wins (forces the page),
matching the spec's explicit "the more specific transition determines the outcome" rule. All of this
was verified empirically against the installed WeasyPrint before committing to the design, following
the same discipline established in `005-page-breaks`.

## Technical Context

**Language/Version**: Python 3.12+ (shared with features 001–005)

**Primary Dependencies**: None new — same Jinja2/WeasyPrint stack as `002`/`005`.

**Storage**: N/A — `column_reset` markers are ordinary entries in existing `content.yaml` files,
exactly like `005`'s `page_break`.

**Testing**: pytest. Unit tests for the generalized segmentation function's break-type tracking
(including the priority-merge rule) and integration tests asserting actual page counts and
left-column landing position for various marker combinations, following `005`'s test conventions.

**Target Platform**: Same as features 001–005 — local dev + CI (Linux), WeasyPrint-rendered PDF.

**Project Type**: Single project — extends the same two files `005-page-breaks` touched:
`templates/cheatsheet.html.j2` and `src/wh40k_cheatsheet/render/html_renderer.py`.

**Performance Goals**: Segmentation remains a single linear pass; no measurable impact on the
existing <10s per-PDF generation budget.

**Constraints**: Must not change behavior for any document using only `page_break` markers or no
markers at all (backward compatible with all `002`/`003`/`005` content, including the real `11e`
content, which now uses one `page_break`). Must not require authors to restructure existing content —
`column_reset` is just one more block type in the same ordered list (FR-011).

**Scale/Scope**: Touches the same two files as `005`; the segmentation function's signature and
return type change (a deliberate, backward-compatible-in-effect evolution: the sole existing call
site, in the template, is updated in the same change).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment |
|-----------|------------|
| I. Code Quality | **Satisfied.** One function evolves (not duplicated); a small, well-named `break_type` field replaces an implicit boolean; ships under the existing gates. |
| II. Testing Standards (NON-NEGOTIABLE) | **Satisfied by design.** Break-type tracking and the priority-merge rule are pure and independently unit-testable; page-count and left-column-position assertions map directly to an integration test, mirroring `005`. |
| III. User Experience Consistency | **Directly served.** Gives maintainers finer-grained pagination control than `005-page-breaks` alone, without the downside of wasted blank pages for minor realignments. |
| IV. Performance Requirements | **Satisfied.** Single linear pass; no measurable overhead. |
| Additional Constraints & Standards | **Satisfied.** No new dependencies; markers are ordinary version-controlled content. |
| Development Workflow & Quality Gates | **Satisfied.** Ships through the same PR-gated workflow as prior features. |

**Verdict**: PASS. No violations; Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/006-column-reset/
├── plan.md                # This file
├── research.md             # Phase 0 output (empirical WeasyPrint findings)
├── data-model.md           # Phase 1 output
├── quickstart.md           # Phase 1 output
├── contracts/
│   └── column-reset-block.md   # The column_reset block contract + priority-merge rule
└── tasks.md                 # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root) — changes to existing files

```text
templates/cheatsheet.html.j2
    # CHANGED:
    #  - {% for segment in group_by_page_breaks(document.blocks) %} becomes
    #    {% for segment in group_by_breaks(document.blocks) %}, and each segment's
    #    <div class="sheet"> gains a conditional "sheet--soft" class when
    #    segment.break_type == "soft"
    #  - new CSS rule: `.sheet + .sheet.sheet--soft { break-before: auto; }`
    #    immediately after the existing `.sheet + .sheet { break-before: page; }` rule
    #  - header comment documents the new `column_reset` block type

src/wh40k_cheatsheet/render/html_renderer.py
    # CHANGED: `group_by_page_breaks` renamed/evolved to `group_by_breaks`, returning
    #  `list[Segment]` (Segment = blocks: list[dict], break_type: "page" | "soft" | None).
    #  Splits on both "page_break" and "column_reset" markers; empty segments dropped
    #  (unchanged from 005); a marker run immediately preceding a segment resolves to
    #  "page" if any marker in that run was page_break, else "soft", else None (only
    #  possible for the very first segment).
    #  Registered as the (renamed) Jinja2 template global.

tests/
├── unit/test_page_breaks.py            # UPDATED: adapted to group_by_breaks()'s new return shape
└── integration/test_page_break_pdf.py  # UPDATED: adapted call sites
├── unit/test_column_reset.py            # NEW: break-type tracking, priority-merge rule
└── integration/test_column_reset_pdf.py # NEW: same-page-when-room, overflow-when-full,
                                           #      left-column landing position, mixed-marker cases
```

**Structure Decision**: No new modules or dependencies. The existing segmentation function is
evolved in place (renamed to reflect its now-broader responsibility) rather than duplicated, since a
single linear pass must consider both marker types together to resolve the priority-merge rule
correctly — two independent passes could not express "page_break wins when adjacent to
column_reset."

## Complexity Tracking

> No constitution violations. Section intentionally left empty.
