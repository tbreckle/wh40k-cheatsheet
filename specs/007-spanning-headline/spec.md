# Feature Specification: Full-Width Spanning Headline

**Feature Branch**: `007-spanning-headline`

**Created**: 2026-08-14

**Status**: Draft

**Input**: User description: "A headline type shall be available that spans both columns, meaning if this special headline type is used the headline and its background shall span both colums so that we have a clear cut and separation on both columns."

## Clarifications

### Session 2026-08-14

- Q: When the spanning treatment is applied to a glossary block via an optional flag, should it affect only the glossary's title bar, or also the layout of its term list? → A: Title-bar only — the glossary's heading spans both columns like a standalone spanning headline; its term list keeps its existing nested two-column layout unchanged.

### Amendment 2026-08-15 (bug fix, reported directly against real content)

Title-bar-only spanning (above) turned out to be a latent bug, not just a design choice: a
non-spanning `.glossary` div long enough to overflow one outer column (e.g. the real 36-term CORE
ABILITIES content) fragments across the outer article's 2-column layout: each fragment
independently applies the glossary's own `column-count: 2`, producing 4 visible narrow columns
instead of 2. This was only caught once the actual `11e` content was visually inspected — the short
fixture content used during original test-writing (2 terms) never grew tall enough to fragment. Fix:
`spanning: true` now applies full-width treatment (`column-span: all`) to **both** the title bar and
the term-list div, so the whole glossary block renders as one full-width, 2-column unit — matching
what "spanning" already visually implied. This supersedes the 2026-08-14 title-bar-only decision;
FR-011/SC-007 and the edge case below are updated accordingly.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Insert a headline that visually spans both columns (Priority: P1)

A maintainer authoring content wants a section heading to visually cut across the entire two-column
layout — its text and background stretching the full width of the page — rather than being confined
to whichever single column it happens to land in, so that heading reads as a clear, deliberate
break between what comes before it and what comes after it.

**Why this priority**: This is the entire value of the feature. Without a way to render a heading
that spans both columns, every heading is confined to one column's width, which cannot provide the
full-width visual separation the maintainer wants. It is a complete, demonstrable capability on its
own.

**Independent Test**: Author content containing one spanning headline placed between two sections,
generate the PDF, and confirm the headline's text and background stretch across the full two-column
width at that position, distinct from the normal single-column headings used elsewhere.

**Acceptance Scenarios**:

1. **Given** content with a spanning headline inserted between two sections, **When** the PDF is
   generated, **Then** the headline's text and its background render across the full width of the
   two-column area, not confined to a single column.
2. **Given** the same content with a normal (non-spanning) heading in the same position instead,
   **When** the PDF is generated, **Then** that heading renders confined to a single column's width,
   visually distinct from the spanning headline's full-width treatment.
3. **Given** a spanning headline placed partway down a page where columns already contain content,
   **When** the PDF is generated, **Then** the spanning headline still renders as a full-width band at
   its position, clearly cutting across both columns.
4. **Given** the existing glossary content type with its spanning option enabled, **When** the PDF is
   generated, **Then** the glossary's own title bar and its term list both span both columns as a
   single full-width, 2-column block — not confined to, or fragmented across, the surrounding
   single-column flow.

---

### User Story 2 - Content on either side of the spanning headline stays correctly placed (Priority: P2)

A maintainer expects that content immediately before and after a spanning headline continues to read
normally — nothing is cut off, duplicated, or displaced — so the full-width headline provides a clean
break without corrupting the surrounding layout.

**Why this priority**: A spanning headline is only useful if it doesn't break the reading experience
around it. This builds on Story 1's core rendering capability by verifying content integrity, but
depends on that capability existing first.

**Independent Test**: Author content with distinct sections immediately before and after a spanning
headline, generate the PDF, and confirm both sections render completely and in their expected reading
order, with the spanning headline providing a clean visual break between them.

**Acceptance Scenarios**:

1. **Given** content immediately before a spanning headline, **When** the PDF is generated, **Then**
   that content renders completely, in its normal column position, unaffected by the headline that
   follows it.
2. **Given** content immediately after a spanning headline, **When** the PDF is generated, **Then**
   that content resumes cleanly in normal column flow below the spanning headline, with no content
   lost or duplicated.
3. **Given** a document with several spanning headlines at different points, **When** the PDF is
   generated, **Then** each one independently provides a clean break, and all surrounding content
   remains correctly placed.

---

### User Story 3 - Spanning headlines behave consistently across every language and edition (Priority: P3)

A maintainer who places a spanning headline in a document expects that same authoring choice to
render identically across every language and edition that shares the same placement, since it is a
structural/visual choice, not translated content.

**Why this priority**: Consistency across languages matters for a polished multi-language product,
but is a refinement on top of Stories 1–2 rather than new core capability.

**Independent Test**: Author a document structure with a spanning headline shared across two
languages, generate both, and confirm the headline renders full-width at the equivalent point in both
generated PDFs.

**Acceptance Scenarios**:

1. **Given** a spanning headline defined as part of a document's shared structure, **When** the PDF is
   generated for any of its supported languages, **Then** the headline spans both columns identically
   at the equivalent point in every language's output.

---

### Edge Cases

- A spanning headline at the very start of the document (before any other content) MUST render
  correctly as a full-width band, not produce an error or unexpected blank area.
- A spanning headline at the very end of the document (after the last content) MUST render correctly
  without producing unexpected blank space afterward.
- A document MAY contain multiple spanning headlines; each MUST independently render as its own
  full-width band.
- A spanning headline MUST remain visually distinct from the standard (single-column) heading style
  already used elsewhere in the document, so authors and readers can tell the two apart.
- A spanning headline MUST coexist correctly with existing pagination features (forced page breaks
  and column realignment) without producing broken or blank layouts when used near them.
- When the existing glossary content type's spanning option is enabled, both its title bar AND its
  term-list div MUST span both columns as one full-width, 2-column block — a non-spanning term list
  can fragment across the outer 2-column layout on long content, doubling its own internal 2 columns
  into 4 visible ones (fixed 2026-08-15).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a headline type, distinct from the standard section heading,
  that an author can use to render a heading spanning the full width of the two-column layout.
- **FR-002**: When the spanning headline type is used, both its text and its background MUST render
  across the complete two-column width at that position, not confined to a single column.
- **FR-003**: The spanning headline MUST be visually distinguishable from the standard single-column
  heading style already used for other headings.
- **FR-004**: Content immediately preceding a spanning headline MUST render completely and in its
  normal position, unaffected by the headline that follows.
- **FR-005**: Content immediately following a spanning headline MUST resume in normal column flow
  below the spanning headline, with nothing lost or duplicated.
- **FR-006**: A document MAY contain any number of spanning headlines; each MUST independently render
  as its own full-width band at its position.
- **FR-007**: A spanning headline at the very start or very end of the document MUST render correctly
  without errors or unexpected blank space.
- **FR-008**: Spanning headline behavior MUST be identical across every supported language and
  edition of a document that shares the same placement.
- **FR-009**: Adding, removing, or repositioning a spanning headline MUST be possible using the same
  authoring process as other content, without requiring a code change.
- **FR-010**: A spanning headline MUST coexist correctly with existing page-break and column-reset
  features, without producing blank pages, blank columns, or broken layout when placed near them.
- **FR-011**: The system MUST provide an optional flag on the existing glossary content type
  (`002-pdf-generation`) that, when enabled, applies the spanning treatment to both the glossary's
  title bar and its term-list — both span both columns as one full-width, 2-column block, rather than
  the term list remaining confined to (and potentially fragmenting within) a single outer column.

### Key Entities *(include if feature involves data)*

- **Spanning Headline**: A maintainer-authored heading, carrying its own title text like a standard
  heading, but rendered so that both its text and background span the full width of the two-column
  layout at its position — creating a clear visual break between the content before and after it.
  Distinct from the standard (single-column) heading used elsewhere in the same document.
- **Glossary (existing, `002-pdf-generation`)**: Gains an optional spanning flag. When enabled, both
  the glossary's title bar and its term-list div render using the same full-width treatment as a
  standalone Spanning Headline; the term *content* itself (text, order, count) is unchanged.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A document using a spanning headline shows that headline's text and background
  stretching across the complete two-column width, in 100% of generations.
- **SC-002**: Content immediately before and after a spanning headline renders completely and in
  correct reading order, with nothing cut off, duplicated, or misplaced, in 100% of generations.
- **SC-003**: A document with multiple spanning headlines renders each one independently and
  correctly.
- **SC-004**: A reader can visually distinguish a spanning headline from a standard heading without
  needing to know which is which in advance.
- **SC-005**: The same spanning headline placement renders equivalently across all languages of a
  given edition.
- **SC-006**: A maintainer can add, move, or remove a spanning headline using the same authoring
  process used for other content, without needing separate tooling or a code change.
- **SC-007**: Enabling the spanning option on a glossary block makes both its title and its term list
  span both columns as one full-width, 2-column block in 100% of generations, while the term-list
  *content* remains identical to the non-spanning case.

## Assumptions

- This feature extends the content-authoring model established in `002-pdf-generation` (ordered
  content blocks rendered through a template) — a spanning headline is one more kind of entry in that
  same ordered structure, authored the same way as other content (e.g., carrying a `title`, similar
  to the existing standard heading block).
- The spanning headline is a **visible content block** (it has its own heading text), not a
  structural marker like the page-break or column-reset markers from prior features — it occupies a
  position in the reading flow and displays content, rather than only affecting layout invisibly.
- Exact visual styling (colors, spacing, typography) is a design decision deferred to planning; this
  spec requires only that the spanning headline's text and background span the full two-column width
  and remain visually distinguishable from the standard heading.
- This feature must remain compatible with the existing page-break (`005-page-breaks`) and
  column-reset (`006-column-reset`) features, since a spanning headline may realistically be
  authored near either.
- Spanning headline content is edition/revision content, so it is versioned and reviewed the same way
  as the rest of the cheat sheet's source content, consistent with the project constitution's
  traceability expectations.
- The glossary spanning flag is opt-in and defaults to off, so every existing glossary block in
  already-authored content (e.g., the real `11e` cheat sheet) continues to render exactly as it does
  today unless a maintainer explicitly enables it.

## Dependencies

- Depends on `002-pdf-generation` for the ordered content-block model and PDF rendering pipeline that
  this feature adds a new block kind to.
- Must remain compatible with `005-page-breaks` and `006-column-reset`, whose pagination/column
  markers may be authored near a spanning headline.
