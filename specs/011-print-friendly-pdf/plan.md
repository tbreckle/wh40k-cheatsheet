# Implementation Plan: Print-Friendly PDF Flag

**Branch**: `011-print-friendly-pdf` | **Date**: 2026-08-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/011-print-friendly-pdf/spec.md`

## Summary

Add an opt-in `--print-friendly` flag to `generate` that produces an additional PDF (and its
retained intermediate HTML) rendered entirely in black/white/grey, with the background logo
watermark omitted, alongside the existing standard colored PDF. The rendering difference is
confined to the template: a new `document.print_friendly` boolean context flag (default `false`,
fully backward-compatible) drives (a) a `body.print-friendly` CSS block that overrides every
existing color custom property with a grayscale equivalent, and (b) a Jinja conditional that omits
the `.page-watermark <img>` entirely rather than merely hiding it. The pipeline renders and writes
this second HTML/PDF pair only when the flag is set, to `<language>-print.html`/`<language>-print.pdf`
— sibling files that never overwrite the standard `<language>.html`/`<language>.pdf`. No new
dependency, no change to content authoring, no change to default (flag-omitted) behavior.

## Technical Context

**Language/Version**: Python 3.12+ (shared with features 001–010; no change)

**Primary Dependencies**: None new — same Jinja2/WeasyPrint stack used since feature 002. The
grayscale palette is expressed as plain CSS custom-property overrides; no image-processing or
PDF-post-processing library is introduced.

**Storage**: N/A — `images/logo_40k.png` remains the sole source asset, referenced only by the
standard rendering; the print-friendly rendering never references it.

**Testing**: pytest. New integration tests render real content with `print_friendly=True` via
WeasyPrint's box-tree API (same technique as `tests/integration/test_page_logo_pdf.py`) to assert:
every element's computed `background_color`/`color`/`border-color` is grayscale (R == G == B,
including fully transparent/`currentColor` cases excluded appropriately); the watermark `<img>`
box is absent from the page tree entirely (not merely invisible); page count and extracted text
content match the standard rendering exactly for the same (edition, revision, language); and the
existing `.pdf_path`/`.html_path` outputs are unaffected when the flag is omitted (regression,
extending `test_reproducible.py`'s byte-identical-output guarantee). A CLI-level test extends
`test_generate_single.py`'s pattern to assert both output files exist and are reported when
`--print-friendly` is passed, and that only the standard file exists when it is not.

**Target Platform**: Same as features 001–010 — local dev + CI (Linux), WeasyPrint-rendered PDF.

**Project Type**: Single project. Touches `templates/cheatsheet.html.j2` (new grayscale CSS block +
conditional watermark), `src/wh40k_cheatsheet/pipeline.py` (`generate`/`_generate_one` gain a
`print_friendly` parameter and a second render/write when set), `src/wh40k_cheatsheet/cli.py` (new
`--print-friendly` flag on the `generate` subcommand, plus the extra result line).

**Performance Goals**: One additional HTML render + PDF conversion per (edition, revision,
language) only when the flag is explicitly passed; existing ~6s/all-languages budget (10s ceiling)
is unaffected when the flag is omitted, and doubling render work for an opt-in flag stays well
within that ceiling given the document's small size.

**Constraints**: Must not alter any existing output byte when the flag is omitted (FR-008,
SC-004's second half). Must never overwrite the standard PDF/HTML with the print-friendly variant
or vice versa (FR-006). Must keep the four stratagem-timing variants and the two callout variants
distinguishable without color (FR-005) — satisfied primarily by the icon/text labels each variant
already carries (▶/◀/◆ and "YOUR TURN"/"OPPONENT'S TURN"/"EITHER PLAYER'S TURN"; ⚠/ℹ), reinforced
by distinct grey shades per variant in the new palette.

**Scale/Scope**: One new CSS block (~15 custom-property overrides under a single `body.print-friendly`
selector) and one conditional wrapper around the watermark `<img>` in the template; a `print_friendly`
parameter threaded through `generate`/`_generate_one` in the pipeline, one new CLI flag, one new
`GeneratedDocument` field, one new CLI output line. No changes to content authoring schema, no new
block types, no changes to any existing `content.yaml`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment |
|-----------|------------|
| I. Code Quality | **Satisfied.** Small, single-responsibility additions: one CSS override block, one Jinja conditional, one threaded boolean parameter. No duplicated logic — the print-friendly render reuses the exact same template and pipeline functions, differing only via the context flag. |
| II. Testing Standards (NON-NEGOTIABLE) | **Satisfied by design.** New integration tests assert grayscale-only computed styles, watermark absence, content/structure parity with the standard rendering, and byte-identical unaffected output when the flag is omitted — mirroring the box-tree assertion technique already established in `test_page_logo_pdf.py`. |
| III. User Experience Consistency | **Satisfied.** Terminology, structure, and layout are unchanged; the four stratagem-timing and two callout variants remain distinguishable without color via their existing icon/text labels, reinforced by distinct grey shades — directly serving the "predictable across equivalent situations" and accessibility (WCAG contrast) requirements. |
| IV. Performance Requirements | **Satisfied.** The extra render/PDF pass only runs when explicitly opted into via the flag; default `generate` behavior and timing are unaffected. |
| Additional Constraints & Standards | **Satisfied.** No new dependency; the grayscale palette is data (CSS values) sourced from the existing template, not a new external asset. |
| Development Workflow & Quality Gates | **Satisfied.** Ships through the same PR-gated `poe check` workflow; no new surface for the `008` docstring gate beyond the two changed Python functions, which will carry the same Google-style docstrings as their neighbors. |

**Verdict**: PASS. No violations; Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/011-print-friendly-pdf/
├── plan.md               # This file (/speckit-plan command output)
├── research.md            # Phase 0 output (/speckit-plan command)
├── data-model.md          # Phase 1 output (/speckit-plan command)
├── quickstart.md          # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── print-friendly-flag.md   # Phase 1 output (/speckit-plan command)
└── tasks.md                 # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root) — changes to existing files

```text
templates/cheatsheet.html.j2
    # CHANGED: every `:root` color custom property now resolves via a server-side Jinja
    #   conditional on a `print_friendly` flag, to its grayscale equivalent (see
    #   data-model.md for the full mapping) — resolved at :root rather than a body-scoped
    #   class override, since @page margin-box content (running header/footer) inherits
    #   custom properties from the page context, not from <body> (found during
    #   implementation; research.md §1 amendment)
    # ADDED: `<body class="{{ 'print-friendly' if print_friendly else '' }}">` — retained
    #   for self-documentation; no CSS rule depends on it
    # CHANGED: the `.page-watermark <img>` tag is now wrapped in
    #   `{% if not print_friendly %}...{% endif %}` — omitted entirely (not merely hidden)
    #   in the print-friendly rendering
    # CHANGED: header doc comment updated to document the new `print_friendly` context key

src/wh40k_cheatsheet/pipeline.py
    # CHANGED: `generate()` gains a `print_friendly: bool = False` parameter, passed through
    #   to `_generate_one()`
    # CHANGED: `_generate_one()` writes the standard HTML/PDF as before; when
    #   `print_friendly` is set, additionally renders HTML with
    #   `{**context, "document": {**context["document"], "print_friendly": True}}` and
    #   writes it to `{language}-print.html` / `{language}-print.pdf` in the same `out_dir`
    # CHANGED: `GeneratedDocument` gains a `print_pdf_path: Path | None` field (`None`
    #   unless `print_friendly` was requested for that document)

src/wh40k_cheatsheet/cli.py
    # CHANGED: `generate` subparser gains `--print-friendly` (`action="store_true"`,
    #   default `False`)
    # CHANGED: `_cmd_generate()` passes `args.print_friendly` through to `generate()` and
    #   prints an additional result line per document when `doc.print_pdf_path` is set

tests/integration/test_print_friendly_pdf.py
    # NEW: grayscale-only computed-style assertions, watermark-absence assertion,
    #   content/page-count parity with the standard rendering, CLI output-line assertions,
    #   and a flag-omitted regression check
```

**Structure Decision**: Single project, same layout as features 002–010. The template carries the
entire visual difference (a CSS override block + one conditional); the two Python changes are
threading a boolean through the existing render/write call already made once per document, made
again under the new flag — no new module, no new abstraction.

## Complexity Tracking

> No constitution violations. Section intentionally left empty.
