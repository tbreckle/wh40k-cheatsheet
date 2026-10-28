# Contract: `section` Marker Block

Feature: [spec.md](../spec.md) · Plan: [plan.md](../plan.md) · Data model: [data-model.md](../data-model.md) ·
Related: [cli-skip-flags.md](./cli-skip-flags.md)

A structural content marker that states which sheet section the following blocks belong to, so
`generate --skip-*` can omit sections independently of translated titles.

---

## Authoring contract

```yaml
document:
  blocks:
    - type: section
      id: core-rules                 # one of: core-rules, core-abilities,
    - type: phase                    #         datasheet-characteristics, core-stratagems
      title: "1. COMMAND PHASE (08)"
    # ...
    - type: section
      id: core-stratagems            # placed BEFORE this section's own page_break
    - type: page_break
    - type: spanning_headline
      title: "STRATAGEMS"
```

| # | Guarantee | Basis |
|---|-----------|-------|
| A1 | `{type: section, id: <id>}` starts a section; its region runs until the next `section` marker or the end of `document.blocks` | data-model.md §2, §3 |
| A2 | `id` is language-independent: the same four ids are used in every language's content, whatever the section's translated title | FR-007; FR-013 |
| A3 | A section's own leading `page_break`/`column_reset` go **after** its marker, so they're omitted together with the section | FR-005; research.md §2, §4 |
| A4 | A section an edition doesn't have is simply not marked (10e has no `datasheet-characteristics` marker) | FR-009 |
| A5 | Adding, moving, or removing a marker is a content-only change; no code change needed | Consistency with 005/006/007 authoring model |

## Validation contract

Applied by `resolve_content` whenever a document contains at least one `section` marker. Each
violation raises `ContentError` naming the content file and the offending id or position.

| # | Guarantee | Basis |
|---|-----------|-------|
| V1 | Every marker's `id` is present and is one of the four section ids | FR-013 |
| V2 | Each id appears at most once per document | FR-013; SC-006 (exactly one section per block) |
| V3 | The first block of `document.blocks` is a `section` marker, so no block precedes the first section | FR-013; SC-006 |
| V4 | A document with **zero** markers is valid and renders as before; but requesting any skip against it raises `ContentError` ("has no section markers; cannot skip sections") | research.md §5; cli-skip-flags.md F4 |
| S1 | Every **shipped** content file (all editions, revisions, languages) contains markers satisfying V1–V3, enforced by `tests/integration/test_section_markers_shipped_content.py` | FR-013; SC-006 |

## Render contract

| # | Guarantee | Basis |
|---|-----------|-------|
| M1 | A `section` marker is never rendered and never starts a new segment: `group_by_breaks()` skips it the same way it strips `page_break`/`column_reset`, without splitting | research.md §3 |
| M2 | Inserting `section` markers into content leaves the rendered HTML byte-identical to the same content without them | FR-006; SC-003 |
| M3 | When a section is skipped, its whole region (marker, content, and its own breaks) is removed before segmentation; the remaining breaks segment exactly as specified by `005-page-breaks`/`006-column-reset`, so no blank page or empty column appears | FR-003; FR-005; SC-002 |
| M4 | Markers of sections that are *not* skipped stay in the block list and are transparent per M1 | data-model.md §5 |
| M5 | The remaining sections keep their content, order, and styling; a section with no break of its own flows on directly after the previous remaining section (e.g. datasheet characteristics after core rules when core abilities is skipped) | FR-004; research.md §4 |

---

## Shipped content placement (implementation detail, documented for traceability)

| Content file | `core-rules` | `core-abilities` | `datasheet-characteristics` | `core-stratagems` |
|---|---|---|---|---|
| `editions/11e/2026-06-01-00/en` | top of `blocks` | before the `page_break` preceding CORE ABILITIES | before the DATASHEET CHARACTERISTICS glossary | before the `page_break` preceding STRATAGEMS |
| `editions/11e/2026-06-01-00/de` | top of `blocks` | before the `page_break` preceding KERNFÄHIGKEITEN | before the DATENBLATT-KENNWERTE glossary | before the `page_break` preceding GEFECHTSOPTIONEN |
| `editions/10e/2026-06-16-00/de` | top of `blocks` | before the `column_reset` preceding KERNFÄHIGKEITEN | - (absent) | before the `page_break` preceding GEFECHTSOPTIONEN |
