# Phase 1 Data Model: Alphabetical Core Abilities Glossary

This feature adds no persistent data entities, no `content.yaml` field, and no schema change. Its
"data" is (a) the existing glossary entry shape, unchanged, and (b) a derived, in-memory sort key
that never appears in output. Both are documented below in place of a traditional
entity/relationship model.

## 1. Glossary Entry (existing shape — unchanged)

Authored in `content.yaml` under a `glossary` block's `terms` list. This feature reads it and
reorders the list; it never writes, rewrites, or adds a field.

| Field | Type | Required | Role in this feature |
|---|---|---|---|
| `term` | `str` | yes (in practice — the template dereferences it unconditionally) | **The sole sort key source.** Folded per §2 to produce the ordering. |
| `text` | `str` | one of `text`/`html` | Ignored by ordering; carried through untouched. |
| `html` | `str` | one of `text`/`html` | Ignored by ordering; carried through untouched. Still injected via `\| safe` exactly as before. |

The enclosing `glossary` block's other fields (`title`, `spanning`) are untouched, and its
behaviour stays as specified in
[`specs/007-spanning-headline/contracts/glossary-spanning-flag.md`](../007-spanning-headline/contracts/glossary-spanning-flag.md).

**Defensive handling**: if an entry is not a mapping, or its `term` is missing or not a string, it
sorts as the empty key (first) rather than raising. Ordering a glossary is not the right place to
fail a build over malformed content; the template's own `StrictUndefined` dereference of `g.term`
remains the loud failure for a genuinely missing term, exactly as today.

## 2. Sort Key (derived, in-memory only)

For each entry, `_sort_key` derives a comparison string from `term`:

| Step | Operation | Purpose | Example (`TÖDLICHE`) |
|---|---|---|---|
| 0 | strip a single leading `[`, if present (2026-09-13 amendment, FR-011) | Weapon-ability terms like `[ANTI-X Y+]` sort under their first letter instead of clustering before every term (`[` is U+005B, which folds before all lowercase letters) | n/a — `TÖDLICHE` has no leading `[` |
| 1 | `str.casefold()` | Case-insensitive ordering (FR-004); also expands `ß` → `ss`, matching German DIN 5007-1 | `tödliche` |
| 2 | `unicodedata.normalize("NFD", …)` | Split precomposed accented characters into base + combining mark | `to` + `◌̈` + `dliche` |
| 3 | drop chars where `unicodedata.combining(c)` is truthy | Leaves the base letter, so accented characters sort under it (FR-003) | `todliche` |

Step 0 only ever removes the term's first character, and only when it is literally `[` — a `[`
anywhere else in the term (including a trailing bracketed gloss like `STURM (Assault)`'s parens, or
an interior `[`) is left untouched and reaches step 1 unchanged.

Ties (two entries whose derived keys are equal, including genuinely duplicate terms) keep their
authored relative order, because Python's `sorted()` is stable — this is what makes FR-005's
determinism guarantee hold without an explicit index tie-breaker.

**Worked examples from real content:**

| Term | Derived key | Effect |
|---|---|---|
| `ÜBERSCHWERER LÄUFER` | `uberschwerer laufer` | Sorts under `U`, between `TÖDLICHE TREFFER` and `VERHEERENDE WUNDEN` — not after `Z`, which naive codepoint order would give |
| `TÖDLICHE EXPLOSION X` | `todliche explosion x` | Sorts under `TO`, adjacent to `TÖDLICHE TREFFER` |
| `PRÄZISION` | `prazision` | Sorts under `PRA`, before `PSYCHISCH` |
| `ANFÜHRER / UNTERSTÜTZUNG` | `anfuhrer / unterstutzung` | Sorts under `ANF`, first in the German 11e list |
| `STURM (Assault)` | `sturm (assault)` | German term drives placement; the bracketed English gloss can only ever tie-break |
| `SCOUTS X"` | `scouts x"` | Sorts under `S`; the trailing quote is never reached in comparison |
| `ANTI-X Y+` | `anti-x y+` | Punctuation retained (research.md §2); sorts under `A` |
| `[ANTI-X Y+] (24.03)` | `anti-x y+] (24.03)` | Leading `[` stripped (step 0, 2026-09-13); sorts under `A`, interleaved with unbracketed terms rather than clustered before them |

The key is computed during rendering and discarded — it is never serialized into HTML, PDF, or any
content file.

## 3. Transformation

| Aspect | Guarantee |
|---|---|
| Signature | `sort_glossary_terms(terms: list[Any]) -> list[Any]` |
| Purity | Returns a **new** list; the input list and every entry mapping inside it are left unmutated (the same entry objects are reused by reference, not copied — nothing writes to them) |
| Cardinality | Output length always equals input length — no entry is dropped, added, or merged |
| Payload | Entry contents (`text`/`html`, and any other key) are byte-identical to the input; only list position changes (FR-006) |
| Identity cases | Empty list → empty list; single entry → same single entry; already-alphabetical list → same order (proved for 11e English, SC-005) |
| Determinism | Same input always yields the same output, on every platform and run — no locale, environment, or randomness involved (FR-005/SC-003) |

## 4. Render Context

No new render-context key. `sort_glossary_terms` is registered as a Jinja2 **global function**
(not a document field), alongside the existing `group_by_breaks`, and is called from the glossary
branch of `templates/cheatsheet.html.j2`. Since the print-friendly pass re-renders the same context
through the same template, it inherits the ordering with no additional wiring (FR-008).
