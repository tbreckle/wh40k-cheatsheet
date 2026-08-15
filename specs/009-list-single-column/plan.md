# Implementation Plan: List Single-Column (Full-Width) Flag

**Branch**: `009-list-single-column` | **Date**: 2026-08-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/009-list-single-column/spec.md`

## Summary

The existing `list` content block gains an optional `single_column` flag that, when set, makes the
list render across the complete width of both of the sheet's columns instead of being confined to
one — reusing the exact `column-span: all` CSS mechanism already shipped for `spanning_headline`
(`007-spanning-headline`) and the glossary's `spanning` flag, applied to the `list` block's existing
`<div class="block">` wrapper via a new `.block--full-width` class. The mechanism was verified
end-to-end against the real template and the actually-installed WeasyPrint before committing to this
design (research.md §1): a flagged list rendered at ≈735pt wide versus ≈351–365pt for a standard,
column-confined list and its surrounding paragraphs, with content order and nested sub-item
rendering unaffected. No new dependency, no new architecture — one more conditional class in the
existing `render_block` macro's `list` branch, exactly like `007`'s and its glossary extension's
one-line changes.

## Technical Context

**Language/Version**: Python 3.12+ (shared with features 001–008)

**Primary Dependencies**: None new — pure CSS/template addition on the existing Jinja2/WeasyPrint
stack from `002-pdf-generation`, reusing the `column-span: all` mechanism from `007`.

**Storage**: N/A — `single_column` is an ordinary optional field on an existing `list` block entry
in `content.yaml`, using the same `document.blocks` convention as every other block type/flag.

**Testing**: pytest. Integration tests asserting a flagged list's rendered box width approximates
the full page content width (vs. a standard list's single-column width), that surrounding content is
unaffected and stays in order, that nested sub-items still render correctly, and that the flag
coexists correctly with `page_break`/`column_reset` — following the box-inspection methodology
established in `006`/`007`/`008`.

**Target Platform**: Same as features 001–008 — local dev + CI (Linux), WeasyPrint-rendered PDF.

**Project Type**: Single project — extends `templates/cheatsheet.html.j2` only. No changes to any
Python module; this is a template-and-CSS-only feature, same shape as `007`.

**Performance Goals**: `column-span` is a standard, cheap CSS layout feature (already proven
negligible-cost in `007`); no measurable impact on the existing <10s per-PDF generation budget.

**Constraints**: Must not alter rendering for any existing `list` block or any document that doesn't
use the new flag (backward compatible with all prior content, including the real `11e` content,
which uses `list` blocks today without the flag). Must remain visually consistent with the document's
existing full-width visual language (FR-005) — reuses the same mechanism as `spanning_headline`
rather than inventing a second, differently-behaving "full width" concept.

**Scale/Scope**: One new optional boolean field (`single_column`) on the existing `list` block, one
new CSS rule (`.block--full-width { column-span: all; }`), one conditional class in one existing
macro branch. No limit on how many lists in a document may use the flag.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment |
|-----------|------------|
| I. Code Quality | **Satisfied.** Minimal, template-only addition; one new CSS rule; no new Python code at all — smaller in scope than `007`'s already-lean single-file change. |
| II. Testing Standards (NON-NEGOTIABLE) | **Satisfied by design.** Box-width/order assertions map directly to FR-001–FR-004; coexistence tests with `005`/`006` markers follow the already-proven orthogonal architecture from `007`/`008`. |
| III. User Experience Consistency | **Directly served.** FR-005 explicitly requires the new full-width layout to look and behave like the document's existing full-width elements — this principle is the requirement, not just a constraint on it. |
| IV. Performance Requirements | **Satisfied.** `column-span` is a standard, inexpensive CSS feature, already measured as negligible-cost in `007`. |
| Additional Constraints & Standards | **Satisfied.** No new dependencies; content stays version-controlled and structure-only where applicable. |
| Development Workflow & Quality Gates | **Satisfied.** Ships through the same PR-gated workflow as prior features; docstrings for any touched Python code (none expected) would follow `008`'s now-enforced gate. |

**Verdict**: PASS. No violations; Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/009-list-single-column/
├── plan.md               # This file
├── research.md            # Phase 0 output (empirical column-span verification on a list wrapper)
├── data-model.md          # Phase 1 output
├── quickstart.md          # Phase 1 output
├── contracts/
│   └── list-single-column-flag.md   # The list single_column flag contract
└── tasks.md                 # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root) — changes to existing files

```text
templates/cheatsheet.html.j2
    # CHANGED (only file touched):
    #  - the `list` branch in the `render_block` macro's dispatch chain gains a conditional
    #    `block--full-width` class on its wrapper `<div class="block">`, applied when
    #    `block.single_column` is truthy: `{{ ' block--full-width' if block.single_column |
    #    default(false) else '' }}` — `| default(false)` guard for StrictUndefined, matching
    #    the glossary `spanning` flag's exact pattern (008-adjacent 007 amendment)
    #  - new CSS rule: `.block--full-width { column-span: all; }`
    #  - header doc comment documents the new `single_column` field on the `list` block type

tests/
└── integration/test_list_single_column_pdf.py   # box-width assertions, surrounding-content
                                                     # integrity, nested sub-item rendering,
                                                     # coexistence with page_break/column_reset
```

**Structure Decision**: A single-file change to `templates/cheatsheet.html.j2` — no Python code is
touched at all, identical in shape to `007-spanning-headline` and its glossary-flag extension. This
is the leanest possible design for this feature.

## Complexity Tracking

> No constitution violations. Section intentionally left empty.
