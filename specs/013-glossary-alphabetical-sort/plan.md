# Implementation Plan: Alphabetical Core Abilities Glossary

**Branch**: `013-glossary-alphabetical-sort` | **Date**: 2026-09-02 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/013-glossary-alphabetical-sort/spec.md`

## Summary

Order every `glossary` block's terms alphabetically at render time, so the generated cheat sheet is
alphabetical regardless of the order terms are authored in. The ordering is produced by one new
pure function, `sort_glossary_terms()`, registered as a Jinja2 global exactly like the existing
`group_by_breaks()` and called from the template's glossary branch. Its sort key folds each term to
a comparable form — casefold, NFD-decompose, drop combining marks — so `Ö` sorts with `O`, `Ä` with
`A`, `Ü` with `U`, and `ß` with `ss` (`str.casefold()` expands it), which is precisely German dictionary (DIN 5007-1) ordering and
leaves ASCII English ordering untouched. Python's stable `sorted()` supplies the tie-breaking
guarantee for identical terms. No new dependency (stdlib `unicodedata`), no `content.yaml` schema
change, no CSS change, no change to any existing block's rendering. Verified against real content:
the English 11e glossary is byte-identical after sorting (already authored alphabetically), while
both German glossaries — currently in English source order — are correctly reordered, including
`ÜBERSCHWERER LÄUFER` landing between `TÖDLICHE TREFFER` and `VERHEERENDE WUNDEN` rather than after
`ZUSÄTZLICHE ATTACKEN`.

## Technical Context

**Language/Version**: Python 3.12+ (shared with features 001–012; no change)

**Primary Dependencies**: None new. Sorting uses stdlib `unicodedata` only; the Jinja2/WeasyPrint
stack is unchanged. Deliberately avoids `locale.strxfrm` (needs OS locales installed, mutates
global process state), PyICU, and `pyuca` — see research.md §1.

**Storage**: N/A — content stays in the existing per-edition `content.yaml` files, unmodified.

**Testing**: pytest. Unit tests (`tests/unit/test_glossary_order.py`, mirroring the existing
`test_page_breaks.py`/`test_column_reset.py` pattern for `group_by_breaks`) cover the sort function
directly: alphabetical result, diacritic folding (`Ö`/`Ä`/`Ü`/`ß`), case-insensitivity, stability
for duplicate terms, entry preservation (count and payload), empty/single-term lists, and a missing
or non-string `term` key. Integration tests
(`tests/integration/test_glossary_order_cross_language.py`, mirroring
`test_column_reset_cross_language.py`) render the real `11e`/`10e` content in every declared
language and assert every adjacent pair of rendered terms is correctly ordered, that the rendered
term count and definition texts match the authored ones exactly, and that the English 11e output is
unchanged by the feature. `test_reproducible.py` already covers determinism across runs.

**Target Platform**: Same as features 001–012 — local dev + CI (Linux), WeasyPrint-rendered PDF.

**Project Type**: Single project. Adds `src/wh40k_cheatsheet/render/glossary.py`; touches
`src/wh40k_cheatsheet/render/html_renderer.py` (register the new global),
`templates/cheatsheet.html.j2` (call it in the glossary branch + header comment note), and
`docs/CONTENT_AUTHORING.md` (FR-010).

**Performance Goals**: One `sorted()` over ~33 terms per glossary block per render — microseconds
against a multi-second WeasyPrint pass. The existing whole-run budget is unaffected.

**Constraints**: Must not alter English 11e output (FR-006/SC-005 — confirmed empirically before
writing this plan). Must preserve every entry and its markup untouched, changing position only
(FR-006). Must be deterministic across runs and platforms, which rules out any locale- or
environment-dependent collation (FR-005/SC-003). Must leave the `spanning` full-width behaviour and
`page_break`/`column_reset` interaction exactly as specified in
`specs/007-spanning-headline/contracts/glossary-spanning-flag.md` (FR-009).

**Scale/Scope**: One new ~30-line module with a single public function, one line registering it as
a Jinja global, one changed line in the template's glossary loop, one template comment update, one
docs paragraph. Three glossary blocks exist in the repository today (11e en, 11e de, 10e de), 31–33
terms each.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment |
|-----------|------------|
| I. Code Quality | **Satisfied.** One new module with a single public function and one private sort-key helper — each with one responsibility. Ordering logic lives in exactly one place, consumed by the template rather than duplicated per call site. Fully type-annotated with Google-style docstrings, matching the `008` docstring gate. |
| II. Testing Standards (NON-NEGOTIABLE) | **Satisfied by design.** New behaviour ships with unit tests covering the expected ordering plus boundary and failure cases (empty list, single term, duplicate terms, missing/non-string `term`, `ß`, umlauts), and cross-language integration tests asserting ordering and entry-preservation against the real shipped content. The data-integrity angle the constitution calls for — that no entry is lost or altered — is an explicit assertion, not an implicit hope. |
| III. User Experience Consistency | **Directly serves it.** Alphabetical order is the predictable behaviour a reader expects from a glossary, and applying it to every glossary block (rather than special-casing the one titled "CORE ABILITIES") keeps the same content type behaving the same way everywhere. Terminology is untouched — sorting moves entries, never rewords them. |
| IV. Performance Requirements | **Satisfied.** A single sort over ~33 short strings per render is immeasurable against the existing PDF pass; no new I/O, no per-lookup cost at read time. |
| Additional Constraints & Standards | **Satisfied.** No new runtime dependency (stdlib `unicodedata`). Game data stays in the same version-controlled, human-reviewable YAML, and — importantly — is *not* rewritten by this feature, so content diffs and source attribution stay intact. | 
| Development Workflow & Quality Gates | **Satisfied.** Ships through the same PR-gated `poe check` (format, lint, bandit, ty, pytest) workflow as every prior feature. |

**Verdict**: PASS. No violations; Complexity Tracking not required.

**Post-design re-check (after Phase 1)**: Still PASS. The design settled on one pure stdlib function invoked from the template seam that already exists for `group_by_breaks` — no new dependency, no new abstraction, no schema surface, and no change to any content file. The test plan in research.md §5 covers each functional requirement plus the boundary cases real content does not exercise, satisfying Testing Standards. Nothing in Phase 1 introduced a trade-off needing justification.

## Project Structure

### Documentation (this feature)

```text
specs/013-glossary-alphabetical-sort/
├── plan.md                              # This file (/speckit-plan command output)
├── research.md                          # Phase 0 output (/speckit-plan command)
├── data-model.md                        # Phase 1 output (/speckit-plan command)
├── quickstart.md                        # Phase 1 output (/speckit-plan command)
├── checklists/
│   └── requirements.md                  # /speckit-specify output
├── contracts/
│   └── glossary-term-ordering.md        # Phase 1 output (/speckit-plan command)
└── tasks.md                             # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
src/wh40k_cheatsheet/render/glossary.py
    # NEW: `sort_glossary_terms(terms)` — returns a new list of the same term mappings
    #   ordered by the folded sort key; never mutates its argument, never touches the
    #   entries themselves. Private `_sort_key(term)` implements the fold
    #   (casefold → NFD → drop combining marks) documented in data-model.md §2.

src/wh40k_cheatsheet/render/html_renderer.py
    # CHANGED: `_environment()` registers `sort_glossary_terms` as a Jinja global, exactly
    #   as it already registers `group_by_breaks` (same `# ty: ignore[invalid-assignment]`
    #   rationale applies — see the existing comment there)

src/wh40k_cheatsheet/render/__init__.py
    # CHANGED: re-export `sort_glossary_terms` alongside `RenderError`/`render_html`

templates/cheatsheet.html.j2
    # CHANGED: the glossary branch's loop becomes
    #   `{%- for g in sort_glossary_terms(block['terms'] | default([])) -%}`
    # CHANGED: header doc comment notes that `terms` are rendered alphabetically by `term`
    #   regardless of authored order

docs/CONTENT_AUTHORING.md
    # CHANGED: glossary section states that ordering is produced at generation time and
    #   authors need not maintain alphabetical order by hand (FR-010)

tests/unit/test_glossary_order.py
    # NEW: sort-function unit tests — ordering, diacritic folding, case-insensitivity,
    #   stability on duplicates, entry preservation, empty/single-term, malformed `term`

tests/integration/test_glossary_order_cross_language.py
    # NEW: renders real 11e (en, de) and 10e (de) content; asserts adjacent-pair ordering,
    #   term count and definition-text preservation, and that 11e en output is unchanged
```

**Structure Decision**: Single project, same layout as features 002–012. Ordering is a presentation
concern, so it lives in the render layer and is invoked from the template — the same seam
`group_by_breaks()` already uses for block-level transformation. It deliberately does *not* live in
`content/resolver.py` (which would make loading lie about what the file contains) nor in
`pipeline.py` (which would have to reach into `document.blocks` and duplicate block-type dispatch
the template already owns). Placing it in the template's glossary branch also means the
print-friendly render, which re-renders the same context through the same template, is covered for
free (FR-008).

## Complexity Tracking

> No constitution violations. Section intentionally left empty.
