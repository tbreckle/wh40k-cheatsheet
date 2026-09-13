# Phase 0 Research: Alphabetical Core Abilities Glossary

No `[NEEDS CLARIFICATION]` markers remained in the Technical Context — this feature reuses the
existing Jinja2/WeasyPrint stack unchanged, and the spec's two scope decisions were resolved during
`/speckit-specify` (recorded in spec.md → Assumptions). The open questions were design decisions,
resolved below. Every ordering claim here was verified against the real shipped content before this
plan was written; see §4.

## 1. How to order German terms correctly without a new dependency

**Decision**: Sort by a folded key derived from the term with stdlib `unicodedata` only:

```text
term  →  casefold()  →  NFD normalize  →  drop Unicode combining marks  →  sort key
```

`str.casefold()` gives case-insensitivity (FR-004) and, as a bonus, already expands `ß` to `ss` —
verified: `"STRAßE".casefold() == "strasse"` — which is exactly the German DIN 5007-1 treatment, so
no special case is needed for it. NFD then decomposes `Ö` into `O` + combining diaeresis, and
dropping every character in Unicode category `Mn` leaves the base letter. The result is that `Ä`,
`Ö`, `Ü` sort as `A`, `O`, `U` — German dictionary ordering — while pure-ASCII English terms fold to
themselves and sort exactly as plain `sorted()` would.

**Rationale**: One fold serves both languages in scope, so no per-language collation table or
branching is needed to satisfy FR-003. It is pure, deterministic, and identical on every platform
and CI runner (FR-005/SC-003), depends on nothing outside the standard library, and is roughly five
lines of code. The umlaut handling is not cosmetic here: `ÜBERSCHWERER LÄUFER` in the German 11e
glossary sorts after `ZUSÄTZLICHE ATTACKEN` under naive codepoint comparison (`Ü` is U+00DC, past
`Z`), which is visibly wrong to a German reader; folded, it lands between `TÖDLICHE TREFFER` and
`VERHEERENDE WUNDEN` where it belongs.

**Alternatives considered**:

- *`locale.strxfrm` with `LC_COLLATE=de_DE.UTF-8`*: rejected — requires the specific locale to be
  generated on every machine that builds a PDF (it is absent from stock CI containers, where the
  call silently degrades to `C` collation rather than failing), and `locale.setlocale` mutates
  global, non-thread-safe process state. Both directly conflict with FR-005/SC-003's
  reproducibility requirement, and a silent degradation is the worst possible failure mode for a
  correctness feature.
- *PyICU (full Unicode Collation Algorithm)*: rejected — a heavyweight native dependency requiring
  system ICU libraries, added purely to order ~33 short uppercase strings. The constitution requires
  a new runtime dependency to be justified against the cost of adding it; the stdlib fold produces
  identical output for every term in the repository, so there is nothing to justify.
- *`pyuca` (pure-Python UCA)*: rejected — same "new dependency for no observable difference"
  argument, plus it ships a large collation table and is not actively maintained.
- *Hand-maintained per-language ordering tables in `project.yaml`*: rejected — pushes a solved
  problem onto content authors and translators, adds a schema surface to keep in sync with every new
  language, and is exactly the manual ordering work this feature exists to remove.

**Known limitation, recorded deliberately**: NFD does not decompose letters that are not
diacritic-plus-base, notably `Ø`, `Æ`, `Ð`, `Þ`. Neither language in scope uses them, and adding a
small explicit expansion map is a contained change if a Nordic or Icelandic translation ever lands.
Documented in contracts/glossary-term-ordering.md so it is a known boundary rather than a surprise.

## 2. Whether to ignore punctuation when comparing

**Decision**: No. Compare the folded term as written, punctuation and spaces included.

**Rationale**: Full dictionary collation ignores punctuation at the primary strength level, so
`ANTI-X Y+` would compare as `antixy`. Against the actual content this makes zero difference —
every term is distinguished well before any punctuation is reached — so a punctuation-stripping pass
would be untested, unobservable complexity, which Code Quality argues against. The spec's edge case
is satisfied either way: `SCOUTS X"` sorts under `S`, not among punctuation, because the folding
never reorders leading characters. If content ever gains two terms that differ only after a
punctuation mark, adding a secondary alphanumeric-only key is a localised change to `_sort_key`
alone, and the contract records that possibility.

**Alternatives considered**:

- *Primary key = alphanumerics only, secondary = full folded string, tertiary = authored index*:
  rejected for now — strictly more correct in theory, but produces byte-identical output for all
  three real glossaries, so it buys nothing today at the cost of a less obvious sort key.

## 3. Where the ordering belongs in the pipeline

**Decision**: A pure function in the render layer (`render/glossary.py`), registered as a Jinja2
global in `_environment()` and called from the template's glossary branch — the same seam
`group_by_breaks()` already occupies.

**Rationale**: Ordering is presentation, not content. Doing it in the template means (a) it applies
to every render of every glossary block, including the print-friendly second pass, which re-renders
the same context through the same template — FR-008 satisfied with no extra wiring; (b) block-type
dispatch stays in the one place that already owns it; and (c) the function is a pure
`list → list` transform, unit-testable without touching Jinja2, WeasyPrint, or the filesystem.

**Alternatives considered**:

- *Sort inside `content/resolver.py` when loading `content.yaml`*: rejected — makes "resolve
  content" silently rewrite content, and the resolver deliberately performs only minimal structural
  validation today. It would also make the loaded mapping differ from the file on disk, which is
  confusing when debugging content.
- *Sort in `pipeline.py` before rendering*: rejected — the pipeline would have to walk
  `document.blocks` and re-implement block-type dispatch that the template already performs, and
  `render_html()`'s deliberately generic `context: dict[str, Any]` signature would gain a hidden
  dependency on document shape.
- *A Jinja `|sort(attribute='term')` filter inline in the template*: rejected — Jinja's built-in
  `sort` compares raw strings, which fails the umlaut requirement (FR-003) outright, and inlining a
  custom key expression in a template is neither testable nor readable.
- *Rewrite the `content.yaml` files into alphabetical order once, as a data migration*: rejected —
  fixes today's three files but not tomorrow's edit, leaves every future author and translator
  responsible for manual ordering (defeating User Story 2), and produces a large content diff that
  obscures source attribution in `git blame`.

## 4. Empirical verification of the chosen ordering

Ran the proposed sort key over the three real glossary blocks before committing to this design:

| Content | Terms | Result |
|---|---|---|
| `editions/11e/2026-08-01-00/en/content.yaml` | 33 | **Order unchanged** — already authored alphabetically, confirming SC-005 and FR-006's no-regression requirement |
| `editions/11e/2026-08-01-00/de/content.yaml` | 33 | Reordered from English source order into German dictionary order; `ÜBERSCHWERER LÄUFER` correctly placed between `TÖDLICHE TREFFER` and `VERHEERENDE WUNDEN`; `STROM` before `STURM`; `SCHWEBEN` before `SCHWER` |
| `editions/10e/2026-08-16-00/de/content.yaml` | 31 | Reordered likewise; bracketed English glosses (`STURM (Assault)`) act only as tie-breakers, never as the primary key, as the spec's edge case requires |

No term was lost, duplicated, or altered in any of the three, and no term's diacritic placement
required a special case beyond the fold.

## 5. Leading `[` on weapon-ability terms (2026-09-13 amendment)

**Decision**: Strip a single leading `[` from the term before folding, if present — nothing else.

**Rationale**: Real content (`10e` German glossary: `[ANTI-X Y+] (24.03)`, `[PISTOL] (24.27)`, …)
authors weapon-ability terms with a leading `[`, per WH40K's own printed notation for these
abilities. `[` is U+005B, which folds (via `casefold()`) to itself and compares *before* every
lowercase letter — so under the original fold, every such term sorted ahead of the entire rest of
the glossary regardless of its actual first letter, which is exactly the "unexpected position"
failure mode §2 above already flags for punctuation in general. Unlike §2's decision to leave
interior/trailing punctuation alone (because no real term is affected by it), this bracket *is*
observably wrong against real shipped content, so it warrants a targeted fix rather than being left
as a known boundary.

The fix is deliberately narrow: only a **leading** `[` (i.e. `term[0] == "["`, checked before any
folding) is removed, and only one character. An interior `[`, a trailing bracketed gloss
(`STURM (Assault)` uses parens, not brackets, but the principle is the same), or a term with `]` but
no leading `[` are all left untouched — the fix targets exactly the observed real-content pattern,
nothing broader.

**Alternatives considered**:

- *Strip all `[`/`]` characters anywhere in the term*: rejected — would also touch a hypothetical
  term with an interior bracketed gloss, changing where it sorts in a way not observed in any real
  content and not asked for; the leading-only rule is the minimal fix for the actual problem.
- *Strip any leading punctuation character generally (not just `[`)*: rejected — over-broad relative
  to the concrete, observed case; no other leading-punctuation term exists in shipped content, so
  generalizing now would be speculative complexity with nothing to validate it against.
- *Treat `[...]` as a unit and move it to the end of the term for sorting*: rejected — more complex
  (requires finding the matching `]`, and deciding what happens if none exists) for no additional
  benefit over simply dropping the leading character; the trailing `]` and everything after it
  already sort correctly once the leading `[` no longer dominates the comparison.

## 6. Test strategy

**Decision**: Unit tests against the pure function for behaviour and boundaries; cross-language
integration tests against the real rendered output for the end-to-end guarantee.

**Rationale**: This mirrors how `group_by_breaks()` is already covered
(`tests/unit/test_page_breaks.py` + `tests/integration/test_page_break_cross_language.py`), so the
suite stays self-consistent. The integration layer is what actually proves FR-001 for shipped
content; the unit layer is what pins the edge cases (duplicate terms, malformed `term`, empty list)
that real content does not currently exercise. Determinism across runs (SC-003) is already
guaranteed by the existing `tests/integration/test_reproducible.py` byte-comparison, which needs no
change — an unstable sort would break it automatically.
