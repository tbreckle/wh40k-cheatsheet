# Feature Specification: Alphabetical Core Abilities Glossary

**Feature Branch**: `013-glossary-alphabetical-sort`

**Created**: 2026-09-02

**Status**: Draft

**Input**: User description: "Sorting of core abilities glossary shall be alphabetically by term."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Look up a core ability during a game (Priority: P1)

A player is mid-turn and needs to check what a keyword on their datasheet does. They scan the
Core Abilities glossary on the printed cheat sheet, expecting the entries to run A to Z so they
can jump straight to the right part of the list instead of reading every entry.

**Why this priority**: This is the entire point of the glossary. An unordered list forces a linear
scan of ~35 entries under time pressure, which is exactly the "slower than paper" failure the
cheat sheet exists to avoid.

**Independent Test**: Generate a cheat sheet for any edition/language and read the Core Abilities
glossary top to bottom; every term must appear in alphabetical order relative to the term before
it. Delivers the lookup speed benefit on its own, with no other change needed.

**Acceptance Scenarios**:

1. **Given** a cheat sheet edition whose glossary terms are authored in an arbitrary order,
   **When** the cheat sheet is generated, **Then** the Core Abilities glossary entries appear in
   alphabetical order by term.
2. **Given** the English 11th edition content (already authored alphabetically), **When** the
   cheat sheet is generated, **Then** the glossary reads in exactly the same order as before this
   feature — no entry moves, none is duplicated, none is dropped.
3. **Given** the German content, where translated terms follow the English source order (STURM,
   EXPLOSIV, SPALTEN, NAHBESCHUSS …), **When** the German cheat sheet is generated, **Then** the
   entries appear in German alphabetical order (ANFÜHRER, ANHALTENDE TREFFER X, ANTI-X Y+ …).
4. **Given** a glossary entry whose term carries a diacritic (TÖDLICHE EXPLOSION X, PRÄZISION,
   GEFÄHRLICH), **When** the cheat sheet is generated, **Then** that entry is placed as if the
   diacritic were its base letter (Ö sorts with O, Ä with A), not after all unaccented terms.

---

### User Story 2 - Author or translate glossary entries without policing order (Priority: P2)

A content author adds a new core ability, or a translator renames a term into their language.
They append or edit the entry wherever it is convenient in the content file and the generated
sheet still comes out in order.

**Why this priority**: Valuable, but it only matters once ordering is guaranteed by generation
(P1). Without P1 this story has nothing to stand on.

**Independent Test**: Append a new term at the end of a content file's glossary block, regenerate,
and confirm the term lands in its alphabetical position in the output.

**Acceptance Scenarios**:

1. **Given** an author appends a new term at the end of the glossary block, **When** the cheat
   sheet is generated, **Then** the term appears in its correct alphabetical position, not last.
2. **Given** an author reorders the entries in the content file, **When** the cheat sheet is
   generated, **Then** the output is unchanged — authored order does not affect the result.

---

### Edge Cases

- **Diacritics and umlauts**: German terms (TÖDLICHE, PRÄZISION, GEFÄHRLICH, ANFÜHRER) sort under
  their base letter, matching what a German reader expects from a dictionary.
- **Terms with parenthetical glosses**: German entries carry the English name in brackets, e.g.
  `STURM (Assault)`. Ordering follows the term as written from its first character, so the
  bracketed gloss only ever acts as a tie-breaker.
- **Leading punctuation, digits, and symbols**: terms such as `ANTI-X Y+` and `SCOUTS X"` contain
  hyphens, quotes, and plus signs; these must not push an entry to an unexpected position relative
  to otherwise identical prefixes (`SCOUTS X"` sorts with S, not with punctuation).
- **Mixed or inconsistent capitalisation**: an entry authored as `Deep Strike` must sort next to
  `DEEP STRIKE`-style entries, not in a separate block of lowercase terms.
- **Duplicate or identical terms**: two entries sharing the same term keep their authored order
  relative to each other, so output stays deterministic across runs.
- **Empty or single-entry glossary**: a glossary block with no terms, or one term, renders exactly
  as it does today without error.
- **Term text vs. term name**: only the term name determines position; the definition body
  (plain text or markup) never influences ordering.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST present Core Abilities glossary entries in alphabetical order by
  term in every generated cheat sheet.
- **FR-002**: Ordering MUST be determined solely by the term name; the definition body MUST NOT
  affect an entry's position.
- **FR-003**: Ordering MUST follow the alphabetical conventions of the content's language, so that
  accented and umlauted characters sort under their base letter rather than after the unaccented
  alphabet.
- **FR-004**: Ordering MUST be case-insensitive, so entries differing only in capitalisation are
  not separated into distinct runs.
- **FR-005**: The system MUST produce the same order for the same content on every generation run,
  including for entries whose terms are identical (ties keep their authored relative order).
- **FR-006**: The system MUST preserve every authored entry and its definition exactly — sorting
  changes position only, never content, count, or markup.
- **FR-007**: The order in which entries are authored in the content file MUST NOT affect the
  generated output.
- **FR-008**: Sorting MUST apply to every generated output variant equally (all editions,
  revisions, languages, and the print-friendly variant).
- **FR-009**: Glossary entries MUST continue to render with their existing appearance and layout
  behaviour, including the full-width (`spanning`) presentation, unchanged.
- **FR-010**: The authoring documentation MUST state that glossary order is produced by generation
  and that authors need not maintain alphabetical order by hand.

### Key Entities

- **Glossary block**: a titled collection of core ability entries within a cheat sheet's content,
  optionally presented full-width. Carries the entries whose order this feature governs.
- **Glossary entry**: a single core ability, consisting of a term name (the sort key) and its
  definition body (plain text or markup, never part of the sort key).
- **Content language**: the language a given cheat sheet's content is written in; determines which
  alphabetical convention applies to ordering.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of generated cheat sheets present their Core Abilities glossary in alphabetical
  order, verified across every edition, revision, and language currently in the repository.
- **SC-002**: A reader looking for a known core ability can locate it by alphabetical position
  alone, without reading entries that precede or follow it — confirmed by checking that every
  adjacent pair of entries in the output is correctly ordered.
- **SC-003**: Generating the same content twice produces an identical glossary order, so
  releases stay reproducible.
- **SC-004**: The number of glossary entries and their definition texts are identical before and
  after this change for every existing edition/language, confirming nothing was lost or altered.
- **SC-005**: The English 11th edition glossary output is unchanged by this feature, since it is
  already authored alphabetically.
- **SC-006**: Adding a new glossary entry requires no manual re-ordering of the content file for
  the generated sheet to be correctly ordered.

## Assumptions

- Ordering is applied when the cheat sheet is generated, rather than being enforced as an authoring
  rule that fails the build. This guarantees correct output regardless of how content is authored
  and keeps translation work simple, at the cost of the content file no longer matching output
  order visually.
- The rule applies to every glossary block in the content vocabulary, not only to the block titled
  "CORE ABILITIES". Today each edition/language has exactly one glossary block and it is the Core
  Abilities glossary, so this is equivalent in practice while keeping behaviour consistent if
  further glossaries are added (Constitution III, User Experience Consistency).
- The language recorded in each edition's content determines the alphabetical convention used; the
  languages in scope today are English and German.
- Terms are compared as written, including any bracketed English gloss used in translations; no
  stripping or normalisation of parenthetical content is performed beyond case and diacritic
  folding.
- No new content authoring field is introduced — authors do not opt in or out of sorting, and no
  existing content file needs to change for this feature to take effect.
- Existing glossary presentation features (the `spanning` full-width flag, column and page break
  behaviour) are unaffected and remain as specified in `specs/007-spanning-headline/contracts/glossary-spanning-flag.md`.
