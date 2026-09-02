# Contract: Glossary Term Ordering

Feature: [spec.md](../spec.md) · Plan: [plan.md](../plan.md) · Data model: [data-model.md](../data-model.md)
Related: [glossary-spanning-flag.md](../../007-spanning-headline/contracts/glossary-spanning-flag.md)

Added 2026-09-02. Extends the existing `glossary` block (`002-pdf-generation`) with a rendering
guarantee about the **order** of its `terms`. No authoring surface changes — this contract adds no
field, removes none, and changes no field's meaning.

---

## Authoring contract

Unchanged from `002-pdf-generation`:

```yaml
document:
  blocks:
    - type: glossary
      title: "CORE ABILITIES"
      spanning: true            # optional; defaults to off (feature 007)
      terms:
        - {term: "TORRENT", text: "Automatically hits."}
        - {term: "ASSAULT", text: "Enables Assault Shooting."}
```

- The order terms are written in **no longer affects output**. Authors and translators may append,
  insert, or reorder entries freely; the generated sheet is alphabetical either way.
- No opt-in or opt-out flag exists. Ordering always applies, to every `glossary` block.
- No existing `content.yaml` needs to change for this contract to take effect, and none is rewritten
  by it.

---

## Rendering contract

| # | Guarantee | Basis |
|---|-----------|-------|
| G1 | Terms render in ascending alphabetical order of `term`, in every generated document (FR-001) | `sort_glossary_terms()` applied in the template's glossary branch; asserted per adjacent pair in `tests/integration/test_glossary_order_cross_language.py` |
| G2 | Ordering depends on `term` only; `text`/`html` never influence position (FR-002) | The sort key reads `term` exclusively — data-model.md §2 |
| G3 | Accented characters sort under their base letter — `Ä`→`A`, `Ö`→`O`, `Ü`→`U`, `ß`→`ss` — giving German dictionary (DIN 5007-1) ordering (FR-003) | NFD fold + combining-mark removal after `casefold()`; verified on real `de` content for both editions |
| G4 | Ordering is case-insensitive, so entries differing only in capitalisation are not split into separate runs (FR-004) | `str.casefold()` is the first fold step |
| G5 | Entries with equal keys (duplicate terms) keep their authored relative order, so output is deterministic (FR-005) | Python's `sorted()` is stable; asserted in `tests/unit/test_glossary_order.py` |
| G6 | Every authored entry survives with its content and markup byte-identical — sorting changes position only, never count, text, or `html` (FR-006) | Pure list reordering; input entries reused by reference and never mutated. Asserted as a count-and-payload comparison in the integration test |
| G7 | Authored order has no effect on output: reordering a `content.yaml`'s `terms` produces an identical document (FR-007) | The sort is total over the derived key; independent of input order except for G5 ties |
| G8 | The ordering applies identically to every edition, revision, language, and to the print-friendly variant (FR-008) | Applied in the template, which every render pass — standard and print-friendly — goes through |
| G9 | Glossary appearance, layout, and the `spanning` full-width behaviour are unchanged; `page_break`/`column_reset` interaction is unchanged (FR-009) | Only the loop's iteration order changes; no markup, class, or CSS is touched. Feature 007's G1–G5 continue to hold verbatim |
| G10 | An empty or single-entry `terms` list renders exactly as before, without error | Identity cases of the transform — data-model.md §3 |
| G11 | An entry whose `term` is missing or not a string sorts first rather than raising; the template's existing `StrictUndefined` behaviour on `g.term` is unchanged | Defensive key derivation — data-model.md §1 |

---

## Ordering mechanism (implementation detail, documented for traceability)

The glossary branch's loop gains one call:

```text
{%- for g in sort_glossary_terms(block['terms'] | default([])) -%}
```

`sort_glossary_terms` is registered as a Jinja2 global in `_environment()`
(`src/wh40k_cheatsheet/render/html_renderer.py`), exactly as `group_by_breaks` already is, and is
implemented in `src/wh40k_cheatsheet/render/glossary.py` as a pure function over the derived key:

```text
casefold()  →  NFD normalize  →  drop combining marks  →  compare
```

(`| default([])` guards against `StrictUndefined` when `terms` is absent, as it already did before
this contract.)

---

## Known boundaries

Recorded so they are deliberate limits rather than latent surprises:

- **Non-decomposing letters**: NFD does not split `Ø`, `Æ`, `Ð`, or `Þ` into base + mark, so those
  would sort by codepoint (after `z`). Neither language in scope uses them. A Nordic or Icelandic
  translation would need a small explicit expansion map in `_sort_key` — a contained change, no
  architectural impact. See research.md §1.
- **Punctuation is significant**: unlike full dictionary collation, punctuation and spaces are
  compared rather than ignored, so two terms differing only after a punctuation mark could order
  differently than a strict dictionary would. No such pair exists in any shipped content. Adding a
  secondary alphanumeric-only key would resolve it, localised to `_sort_key`. See research.md §2.
- **No numeric-aware ordering**: `X10` sorts before `X2`, as with any lexicographic sort. No shipped
  term is affected.
