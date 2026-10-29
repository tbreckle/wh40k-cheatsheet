# Implementation Plan: Skip Cheat Sheet Sections on Generation

**Branch**: `015-skip-sheet-sections` | **Date**: 2026-09-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/015-skip-sheet-sections/spec.md`, plus the planning
input: "CLI args should be `--skip-core-rules`, `--skip-core-abilities`,
`--skip-datasheet-characteristics` and `--skip-core-stratagems`".

## Summary

Add four boolean flags to `generate` - `--skip-core-rules`, `--skip-core-abilities`,
`--skip-datasheet-characteristics`, `--skip-core-stratagems` - each omitting one sheet section.
Content files gain a new structural marker block, `{type: section, id: <section-id>}`, that starts
a section and runs until the next marker, following the same flat-marker pattern `page_break` and
`column_reset` already use. The pipeline resolves every requested language's content up front,
drops each skipped section's region (marker, headings, blocks, and its own page/column breaks)
before rendering, and fails before writing anything if a sheet would be left empty. Because
filtering happens *before* `group_by_breaks()`, the existing "leading/consecutive breaks never make
an empty segment" guarantee from `005`/`006` also prevents blank pages. `group_by_breaks()` treats
`section` markers as transparent (no split, never rendered), so content with markers renders
byte-identically to today when no flag is passed. A partial sheet is written to its own file,
`<lang>-no-<omitted-ids…>[-print].{html,pdf}`, never over the full sheet. `package` is unchanged.

## Technical Context

**Language/Version**: Python 3.12+ (shared with features 001–014)

**Primary Dependencies**: None new - argparse, PyYAML, Jinja2, WeasyPrint as today.

**Storage**: The three shipped `content.yaml` files each gain 3–4 `section` marker blocks
(`editions/11e/2026-06-01-00/{en,de}`, `editions/10e/2026-06-16-00/de`).

**Testing**: pytest. Unit tests for section validation, omission, and output naming; integration
tests that render real content and inspect page count and text per `005`/`006`/`007`'s
methodology; a byte-identity test proving markers are invisible in the output.

**Target Platform**: Same as prior features - local dev + CI (Linux), WeasyPrint-rendered PDF.

**Project Type**: Single-project CLI.

**Performance Goals**: Omission is one linear pass over ~110 blocks per sheet; skipping sections
only reduces rendering work. No impact on the existing <10s per-PDF budget.

**Constraints**: With no skip flag, output files and printed result lines must be byte-identical to
today (FR-006/SC-003). Skipped sections must never leave a blank page (FR-005). A partial sheet must
never overwrite the full sheet (FR-012/SC-007). `package` must keep building full sheets (FR-014).

**Scale/Scope**: 4 section ids, 4 CLI flags, 1 new module, 5 changed source files, 3 content files,
1 template doc comment, 1 doc page.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment |
|-----------|------------|
| I. Code Quality | **Satisfied.** One new pure, fully typed module (`content/sections.py`) owns section ids, validation, omission, and naming; the resolver, renderer, pipeline, and CLI each gain a small, single-purpose change. Google-style docstrings per the `008` gate. |
| II. Testing Standards (NON-NEGOTIABLE) | **Satisfied by design.** Unit tests cover the omission transform, marker validation (unknown id, duplicate id, unattributed leading blocks), canonical naming, and the empty-sheet failure. Integration tests cover each flag against real content, no blank pages, byte-identity without flags, print-friendly naming, the 10e no-op, and `package` unchanged. A shipped-content test fails the build if any block is unattributed (principle II's "game data validated against its schema"). |
| III. User Experience Consistency | **Satisfied.** Flags follow the existing kebab-case `--print-friendly` style. Section ids are identical in every language (FR-007). `--skip-core-stratagems` uses the game's own term "Core Stratagems" for this set. The web/mobile/WCAG clauses don't apply to a PDF-generating CLI, as with prior features. |
| IV. Performance Requirements | **Satisfied.** Linear filtering; skipping sections shortens rendering. |
| Additional Constraints & Standards | **Satisfied.** Section membership lives in version-controlled, diffable `content.yaml`; no new dependencies. |
| Development Workflow & Quality Gates | **Satisfied.** Ships through the existing PR-gated workflow and CI. |

**Verdict (pre-research)**: PASS. **Verdict (post-design re-check)**: PASS - the design adds no new
dependency, keeps output byte-identical without flags, and every new behavior has a planned test.
Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/015-skip-sheet-sections/
├── plan.md                           # This file
├── research.md                       # Phase 0 output
├── data-model.md                     # Phase 1 output
├── quickstart.md                     # Phase 1 output
├── contracts/
│   ├── cli-skip-flags.md             # generate's four flags, output naming, failure modes
│   └── section-marker-block.md       # the `section` content marker: authoring + validation
├── checklists/requirements.md        # from /speckit-specify
└── tasks.md                          # Phase 2 (/speckit-tasks - NOT created here)
```

### Source Code (repository root)

```text
src/wh40k_cheatsheet/
├── content/
│   ├── sections.py        # NEW: SECTION_IDS (canonical order), validate_section_markers(),
│   │                      #      omit_sections() -> OmissionResult, output_stem()
│   └── resolver.py        # CHANGED: calls validate_section_markers() on load
├── render/
│   └── html_renderer.py   # CHANGED: group_by_breaks() skips `section` markers (no split)
├── pipeline.py            # CHANGED: generate(..., skip_sections=frozenset()); resolve + omit
│                          #          every language before writing; empty-sheet check;
│                          #          output stem via output_stem(); GeneratedDocument gains
│                          #          omitted_sections
└── cli.py                 # CHANGED: four --skip-* flags on `generate`, mapped to section ids

templates/cheatsheet.html.j2          # CHANGED: header doc comment documents `section` markers
editions/11e/2026-06-01-00/en/content.yaml   # CHANGED: 4 section markers
editions/11e/2026-06-01-00/de/content.yaml   # CHANGED: 4 section markers
editions/10e/2026-06-16-00/de/content.yaml   # CHANGED: 3 section markers (no datasheet-characteristics)
docs/CONTENT_AUTHORING.md             # CHANGED: section markers + --skip-* flags

tests/
├── unit/
│   ├── test_sections.py              # NEW: validation, omission, canonical naming, empty result
│   └── test_page_breaks.py           # CHANGED: `section` markers never split or render
└── integration/
    ├── test_skip_sections_pdf.py     # NEW: per-flag content absence, no blank pages, reflow,
    │                                 #      print-friendly naming, 10e no-op, full sheet untouched
    ├── test_skip_sections_cli.py     # NEW: flag parsing, result lines, all-empty failure,
    │                                 #      unknown flag rejected, package unchanged
    └── test_section_markers_shipped_content.py  # NEW: every shipped block attributed to one
                                                  #      section; markers don't change rendered HTML
```

**Structure Decision**: Keep the existing single-project layout. Section logic lives in a new
`content/sections.py` because sections are a property of content, not of rendering. The resolver
validates markers; the pipeline applies omission, since it already owns per-language iteration and
output naming. The renderer only needs to treat markers as transparent.

## Complexity Tracking

> No constitution violations. Section intentionally left empty.
