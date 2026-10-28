# Phase 1 Data Model: Skip Cheat Sheet Sections on Generation

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md) · Research: [research.md](./research.md)

This feature adds one content block type (a structural marker), one derived structure (a section
region), one CLI-supplied selection, and one pure transformation. There is no persistence beyond
the existing `content.yaml` files and output PDFs.

---

## 1. Sheet Section (fixed vocabulary)

| Canonical order | Section id | CLI flag | 11e `en` title | 11e / 10e `de` title | Present in 10e `de`? |
|---|---|---|---|---|---|
| 1 | `core-rules` | `--skip-core-rules` | *(no single title: phases 1–5, actions, terrain, objectives, …)* | *(same, translated)* | yes |
| 2 | `core-abilities` | `--skip-core-abilities` | CORE ABILITIES | KERNFÄHIGKEITEN | yes |
| 3 | `datasheet-characteristics` | `--skip-datasheet-characteristics` | DATASHEET CHARACTERISTICS | DATENBLATT-KENNWERTE | **no** |
| 4 | `core-stratagems` | `--skip-core-stratagems` | STRATAGEMS + USING STRATAGEMS | GEFECHTSOPTIONEN + GEFECHTSOPTIONEN VERWENDEN (11e) / … REGELN (10e) | yes |

Exposed as `SECTION_IDS: tuple[str, ...]` in canonical order, the single source of truth for flag
mapping, validation, and naming.

## 2. `section` marker block (content.yaml)

| Field | Type | Required | Notes |
|---|---|---|---|
| `type` | `"section"` | yes | Structural marker; never rendered |
| `id` | `str` | yes | One of `SECTION_IDS` |

**Validation rules** (applied by `resolve_content` whenever a document has ≥1 marker; violations
raise `ContentError` naming the content file):

- `id` is present and is one of `SECTION_IDS`.
- Each `id` appears at most once in the document.
- The first block of `document.blocks` is a `section` marker, so no block is unattributed.

A document with **zero** markers is still valid (synthetic/test documents); see §5's error for
skips against such a document.

**Placement convention** (shipped content): one marker at the very top (`core-rules`), and one
immediately **before** each later section's own leading `page_break`/`column_reset`, or before its
first content block if it has no leading break.

```yaml
document:
  blocks:
    - type: section
      id: core-rules
    - type: phase
      title: "1. COMMAND PHASE (08)"
    # ...
    - type: section
      id: core-abilities
    - type: page_break
    - type: column_reset
    - type: glossary
      title: "CORE ABILITIES"
      # ...
    - type: section
      id: datasheet-characteristics
    - type: glossary
      title: "DATASHEET CHARACTERISTICS"
      # ...
    - type: section
      id: core-stratagems
    - type: page_break
    - type: spanning_headline
      title: "STRATAGEMS"
    # ... stratagem cards, column_reset, "USING STRATAGEMS" ...
```

## 3. Section Region (derived, in-memory)

The ordered run of blocks from one `section` marker up to (not including) the next marker or the
end of `document.blocks`, marker included. It contains that section's content blocks and any
`page_break`/`column_reset` inside it. Regions never overlap, and with valid markers every block is
in exactly one region.

A region is **present** in a document iff its marker is. A section is **absent** from a document
(e.g. `datasheet-characteristics` in 10e) iff it has no marker there.

## 4. Section Omission Selection

`frozenset[str]` ⊆ `SECTION_IDS`, built by the CLI from the four flags (empty when no flag is
passed). Passed to `generate(..., skip_sections=...)`. An id outside `SECTION_IDS` →
`PipelineError` (programmatic misuse; the CLI can't produce one).

## 5. Transformation: `omit_sections`

| Aspect | Guarantee |
|---|---|
| Signature | `omit_sections(blocks: list[dict], selection: frozenset[str]) -> OmissionResult` |
| `OmissionResult` | `blocks: list[dict]` (remaining blocks, document order), `omitted: tuple[str, ...]` (ids actually removed, canonical order) |
| Empty selection | Returns the input blocks unchanged (same list contents) and `omitted == ()` |
| Present + selected | The whole region (marker, content, its breaks) is removed; its id is in `omitted` |
| Absent + selected | Nothing removed; id **not** in `omitted` (FR-009) |
| Unselected | Region kept verbatim, marker included (markers are transparent to rendering, research.md §3) |
| Purity | New list; input list and block mappings are never mutated |
| Error | None - `omit_sections` never raises, so `content/sections.py` stays free of resolver imports. The pipeline rejects a non-empty selection on a document with zero markers *before* calling it → `ContentError("<content file path>: content has no section markers; cannot skip sections")` (contracts/cli-skip-flags.md F4) |

**Empty-sheet check** (pipeline, research.md §6): a result whose `blocks` contain nothing except
`section`/`page_break`/`column_reset` blocks counts as empty → `PipelineError` before any output
is written.

## 6. Output file stem

`output_stem(language: str, omitted: tuple[str, ...], *, print_friendly: bool) -> str`

```text
stem = language
if omitted:        stem += "-no-" + "-".join(omitted)   # omitted already in canonical order
if print_friendly: stem += "-print"
```

The HTML and PDF share the stem in `out/<edition>/<revision>/`. Examples are in research.md §7 and
contracts/cli-skip-flags.md O2.

## 7. `GeneratedDocument` (extended)

| Field | Type | Notes |
|---|---|---|
| *(existing)* | | `edition_id`, `revision`, `language`, `html_path`, `pdf_path`, `print_html_path`, `print_pdf_path` |
| `omitted_sections` | `tuple[str, ...]` | New. Canonical order; `()` when nothing was omitted. Paths above already reflect the partial stem |

## 8. Flow

```text
CLI flags ──► selection: frozenset[str]
                    │
generate(config, paths, edition, revision, language, print_friendly, skip_sections=selection)
  ├─ validate selection ⊆ SECTION_IDS                          (PipelineError)
  ├─ for each language: resolve_content()  ── validates markers (ContentError)
  │                     omit_sections()   ── OmissionResult
  │                     empty? ──────────────► PipelineError, nothing written
  └─ for each language: render + write <output_stem(...)>.{html,pdf}
                        (print-friendly: second stem with -print)
                              │
                     group_by_breaks(remaining blocks)  ── markers transparent,
                                                          breaks segmented as in 005/006
```
