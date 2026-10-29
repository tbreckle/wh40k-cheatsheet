# Phase 0 Research: Skip Cheat Sheet Sections on Generation

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md)

The spec left two design questions to planning: the CLI shape, now fixed by the planning input,
and how content identifies which section a block belongs to (FR-013). The rest below follows from
how the pipeline, renderer, and shipped content work today, verified by reading
`render/html_renderer.py`, `content/resolver.py`, `pipeline.py`, `templates/cheatsheet.html.j2`,
and all three shipped `content.yaml` files.

---

## 1. CLI surface

**Decision**: Four independent boolean flags on `generate`, exactly as given in the planning input:
`--skip-core-rules`, `--skip-core-abilities`, `--skip-datasheet-characteristics`,
`--skip-core-stratagems`. Each maps to a section id equal to the flag's suffix: `core-rules`,
`core-abilities`, `datasheet-characteristics`, `core-stratagems`. `package` gains no flags.

**Rationale**: Matches the existing boolean `--print-friendly` style. It is discoverable in
`--help` and trivially composable (FR-002). Deriving section ids from the flag names gives one
vocabulary for flags, content markers, and output file names, instead of three.

FR-010 (reject an unrecognized section, list the valid ones) is covered structurally: argparse
rejects an unknown `--skip-…` flag with exit code 2 and an "unrecognized arguments" error before
any generation, and the usage line lists every valid flag. The programmatic
`generate(skip_sections=…)` entry point separately validates ids against the known set.

Naming a flag twice is harmless (`store_true`), covering the spec's "same section twice" edge case.

**Alternatives considered**:
- *A repeatable `--skip <section>` with `choices=`*: rejected by the planning input's explicit flag
  names. It would have given a slightly richer "invalid choice" message, but offers no behavioral
  difference.
- *Also adding flags to `package`*: rejected - FR-014 requires releases to stay full sheets.

---

## 2. How content declares section membership (FR-013)

**Decision**: A new structural marker block, `{type: section, id: <section-id>}`. A section's
region runs from its marker up to (not including) the next marker, or the end of the document.
Each shipped content file places a marker at the very top (`core-rules`) and before each later
section. The marker goes **before** that section's own leading `page_break`/`column_reset`, so those
breaks belong to the section and disappear with it when it is skipped.

**Rationale**: Today nothing in content marks section boundaries, and the only distinguishing
feature between the two glossaries is their *translated* title ("CORE ABILITIES" /
"KERNFÄHIGKEITEN"). The 10e sheet also has no `page_break` before its abilities glossary, so page
positions can't be used either. A flat marker matches how `page_break`/`column_reset` already work
(research of `005`/`006`). It needs only 3–4 lines per content file, can't be forgotten on a new
block (a block inherits the section of the nearest preceding marker), and keeps the block list flat
for every existing consumer.

**Alternatives considered**:
- *A `section:` key on every block*: ~110 edits per file. Every future block would need to remember
  the key, so an unattributed block would be easy to introduce.
- *Nesting blocks under `sections: [{id, blocks}]`*: restructures every content file and every
  consumer (`group_by_breaks`, the template loop, the glossary-order and page-break tests), for no
  behavioral gain over flat markers.
- *Inferring sections from glossary titles or page breaks*: depends on translated titles, violating
  FR-007/FR-013, and fails outright for 10e.

---

## 3. Markers never render and never change layout

**Decision**: `group_by_breaks()` skips `section` blocks without starting a new segment, exactly as
if they weren't there.

**Rationale**: The template consumes blocks only through `group_by_breaks(document.blocks)` →
`render_block`. An unknown block type falls through `render_block`'s `else` branch to a paragraph,
which would raise under `StrictUndefined` (no `text`). Handling markers inside `group_by_breaks` -
the function that already strips `page_break`/`column_reset` - makes them safe for the pipeline and
for every direct `render_html` caller, including tests. Because a marker never splits a segment,
content with markers renders byte-identically to the same content without them. This is what
guarantees FR-006/SC-003 once the shipped files gain markers.

**Alternatives considered**:
- *Strip markers only in the pipeline*: leaves `render_html` callers, test fixtures, and quickstart
  snippets one missing strip away from a crash.
- *Render markers as empty elements*: would change the HTML bytes (breaking FR-006) and could affect
  multi-column flow.

---

## 4. Where omission happens, and why that prevents blank pages

**Decision**: The pipeline applies omission to `document.blocks` after resolving content and before
rendering, via a pure `omit_sections(blocks, selection)` that removes each skipped section's entire
region, marker included.

**Rationale**: Removing a region before segmentation hands `group_by_breaks()` a block list whose
breaks are just the remaining sections' breaks. `group_by_breaks()` already guarantees that
leading, trailing, or consecutive breaks never produce an empty segment (`005`/`006`), so no blank
page or empty column can appear (FR-005). Worked through against 11e today:

| Skipped | Remaining list starts / joins with | Result |
|---------|------------------------------------|--------|
| core-rules | abilities' own `page_break`, `column_reset` | leading breaks → no empty segment; sheet starts with abilities |
| core-stratagems | ends after datasheet characteristics | stratagems' `page_break` gone; no trailing empty page |
| core-abilities (keep datasheet-characteristics) | core rules → datasheet-characteristics glossary | no break between them (there is none today), so datasheet characteristics flows on directly after core rules |

The last row is a deliberate consequence: sections keep their *own* breaks, and no break is invented
for a neighbour. FR-005 forbids blank pages, not reflow.

**Alternatives considered**:
- *Filtering inside the template*: puts content logic in Jinja and makes the empty-sheet check and
  output naming (§6/§7) impossible to decide before rendering.
- *Synthesising a page break at every section start*: invents layout that isn't in the content and
  would change the full sheet's own pagination.

---

## 5. Marker validation

**Decision**: `resolve_content` validates markers whenever a document contains any. Each marker must
have an `id` that is one of the four section ids. Each id may appear at most once. If any marker is
present, the first block must be a marker, so no block precedes the first section. A document with
no markers stays valid, which keeps synthetic test documents and `render_html` fixtures working,
but requesting a skip against such a document raises `ContentError` ("content has no section
markers"). A dedicated test asserts every **shipped** content file is fully attributed (FR-013,
SC-006).

**Rationale**: Validation at load time fails bad content loudly and early, naming the file, like
every other `ContentError`. Allowing marker-less documents avoids touching dozens of existing
synthetic test documents that have no concept of sections. The shipped-content test is what
actually enforces FR-013 for real data.

**Alternatives considered**:
- *Require markers in every document*: breaks every existing synthetic test document for no
  user-facing benefit.
- *Silently treat a marker-less document as "section absent"*: a skip against unmarked content
  would then quietly do nothing, which hides a content bug.

---

## 6. Empty sheets and the "fail before writing" rule (FR-011)

**Decision**: `generate` first resolves and applies omission for **every** requested language. If
any resulting sheet has no content blocks left (only markers or breaks, or nothing), it raises
`PipelineError` naming the edition, revision, language, and skipped sections, before rendering or
writing any file. Passing all four flags is one such case, but not the only one: 10e has no
datasheet-characteristics section, so skipping the other three also empties it.

**Rationale**: FR-011's intent is "never write a sheet with nothing left". Checking every language
first keeps FR-010/FR-011's "before any output is written" guarantee for multi-language runs;
checking language by language would write `en` and then fail on `de`.

**Alternatives considered**:
- *Check only "all four flags passed"*: would write an empty 10e PDF when three flags are passed.
- *Check per language while generating*: partial output on failure.

---

## 7. Output file naming (FR-012)

**Decision**: The file stem is `<language>`, then `-no-` followed by the **actually omitted** section
ids joined with `-` in canonical sheet order, then `-print` for the print-friendly variant. The
canonical order is `core-rules`, `core-abilities`, `datasheet-characteristics`, `core-stratagems`.
If nothing was actually omitted from a sheet, the stem is `<language>` / `<language>-print`, as
today.

| Flags | 11e `en` standard | 11e `en` print-friendly |
|-------|-------------------|--------------------------|
| none | `en.pdf` | `en-print.pdf` |
| `--skip-core-stratagems` | `en-no-core-stratagems.pdf` | `en-no-core-stratagems-print.pdf` |
| `--skip-core-stratagems --skip-core-rules` | `en-no-core-rules-core-stratagems.pdf` | `en-no-core-rules-core-stratagems-print.pdf` |
| `--skip-datasheet-characteristics` (10e `de`) | `de.pdf` (nothing present to omit) | `de-print.pdf` |

**Rationale**: This implements the 2026-09-15 clarification (option B). Using the flag-derived ids
keeps one vocabulary (§1). Canonical ordering makes names independent of flag order. Naming by
*actual* omission means a no-op skip writes content identical to the full sheet under the full
sheet's name, which is harmless, and a multi-edition workflow never produces a "no-X" file that
contains X's absence by accident. The spec's FR-012 examples were updated to these ids.

**Alternatives considered**:
- *Name by requested flags*: a 10e `de-no-datasheet-characteristics.pdf` would be byte-identical to
  `de.pdf`, a misleading duplicate.
- *Short codes (e.g. `en-no-cr-cs.pdf`)*: shorter, but opaque.

---

## 8. Everything else stays put

- `package_all` calls `generate` without `skip_sections`, so release assets are unchanged (FR-014).
- `GeneratedDocument` gains `omitted_sections: tuple[str, ...]` (canonical order; empty when nothing
  was omitted). The CLI's result-line format is unchanged; lines simply show the partial file paths.
- The INFO "generating edition …" log line appends ` [skip: core-rules, core-stratagems]` when a
  selection is given. It is logged to stderr, so stdout result lines keep `004`'s parity guarantee.

## Resolved unknowns summary

| Unknown | Resolution |
|---------|------------|
| CLI shape | Four boolean `--skip-*` flags (planning input); ids = flag suffixes (§1) |
| How content marks sections | Flat `{type: section, id}` marker blocks, before each section's own breaks (§2) |
| Keeping output identical without flags | Markers are transparent to `group_by_breaks()` (§3) |
| Avoiding blank pages | Omit before segmentation; reuse `005`/`006`'s empty-segment guarantee (§4) |
| Validating attribution | Resolver validates markers; shipped-content test enforces full coverage (§5) |
| Fail-before-write for empty sheets | Resolve and omit every language first; any empty sheet → `PipelineError` (§6) |
| File naming | `<lang>[-no-<actually omitted ids>][-print]`, canonical order (§7) |

No NEEDS CLARIFICATION items remain.
