# Feature Specification: Subphase Heading

**Feature Branch**: `014-subphase-block`

**Created**: 2026-09-13

**Status**: Draft

**Input**: User description: "add another type for subphase (like phase), with a slightly brighter
color compared to phase."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Insert a heading one level below a phase (Priority: P1)

A maintainer authoring content wants a heading for a step nested within a `phase` — e.g. a named
sub-step of a turn phase — that reads as part of the same phase, but as a step below it, without
resorting to the existing `subsection` heading (already used for a different kind of grouping) or a
full-width `spanning_headline` (a much stronger visual break than a nested step needs).

**Why this priority**: This is the entire value of the feature. Without a dedicated heading style one
level below `phase`, a maintainer must either overload an existing heading type or fall back to a
non-heading block, losing the clear visual hierarchy the cheat sheet otherwise maintains.

**Independent Test**: Author content containing a `phase` heading immediately followed by a
`subphase` heading, generate the PDF, and confirm both render as headings in the established visual
language (green bar, white uppercase text), with the `subphase` heading's background visibly
brighter than the `phase` heading's.

**Acceptance Scenarios**:

1. **Given** content with a `phase` heading followed by a `subphase` heading, **When** the PDF is
   generated, **Then** both render as heading bars in the same visual language, and the `subphase`
   bar's background is a visibly brighter shade of the same color family as the `phase` bar.
2. **Given** the same content in print-friendly mode, **When** the PDF is generated, **Then** both
   headings render in grayscale, and remain distinguishable from each other by shade (FR-004).
3. **Given** a document with several `subphase` headings, **When** the PDF is generated, **Then**
   each one independently renders with the same brighter background.

---

### User Story 2 - Subphase headings behave consistently across every language and edition (Priority: P2)

A maintainer who places a `subphase` heading in a document expects that same authoring choice to
render identically (same color, same relative position) across every language and edition that
shares the same placement, since it is a structural/visual choice, not translated content.

**Why this priority**: Consistency across languages matters for a polished multi-language product,
but is a refinement on top of Story 1 rather than new core capability.

**Independent Test**: Author a document structure with a `subphase` heading shared across two
languages, generate both, and confirm the heading renders with the identical brighter background at
the equivalent point in both generated outputs.

**Acceptance Scenarios**:

1. **Given** a `subphase` heading defined as part of a document's shared structure, **When** the PDF
   is generated for any of its supported languages, **Then** the heading renders with the identical
   background color at the equivalent point in every language's output.

---

### Edge Cases

- A `subphase` heading at the very start of the document (before any other content, including
  without a preceding `phase`) MUST render correctly, not produce an error.
- A `subphase` heading at the very end of the document MUST render correctly without producing
  unexpected blank space.
- A document MAY contain any number of `subphase` headings; each MUST independently render with the
  same brighter background.
- A `subphase` heading MUST coexist correctly with existing pagination features (`page_break`,
  `column_reset`) without producing broken or blank layouts when used near them.
- In print-friendly (grayscale) mode, `phase` and `subphase` MUST remain distinguishable from each
  other by grayscale shade, matching the pattern already established for callout and stratagem-timing
  variants (`011-print-friendly-pdf`).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a heading type, `subphase`, distinct from both `phase` and
  `subsection`, that an author can use for a heading nested one level below a `phase`.
- **FR-002**: A `subphase` heading MUST render using the same typography, padding, and width as a
  standard `phase` heading — confined to a single column, not spanning both.
- **FR-003**: A `subphase` heading's background MUST be a visibly brighter shade than a `phase`
  heading's background, while remaining in the same green color family, so the two read as related
  but distinct heading levels.
- **FR-004**: In print-friendly (grayscale) mode, `phase` and `subphase` MUST render as two distinct,
  distinguishable grayscale shades — never resolving to the same shade.
- **FR-005**: A document MAY contain any number of `subphase` headings; each MUST independently
  render with the same brighter background at its position.
- **FR-006**: A `subphase` heading at the very start or very end of the document MUST render
  correctly without errors or unexpected blank space.
- **FR-007**: `subphase` behavior MUST be identical across every supported language and edition of a
  document that shares the same placement.
- **FR-008**: Adding, removing, or repositioning a `subphase` heading MUST be possible using the same
  authoring process as other content, without requiring a code change.
- **FR-009**: A `subphase` heading MUST coexist correctly with existing page-break and column-reset
  features, without producing blank pages, blank columns, or broken layout when placed near them.

### Key Entities *(include if feature involves data)*

- **Subphase Heading**: A maintainer-authored heading, carrying its own title text like a `phase`
  heading, rendered with the same typography/padding/width as `phase` but a visibly brighter
  background — signaling a heading nested one level below a `phase`. Distinct from `subsection`
  (an existing, differently-colored heading level already used for a different kind of grouping) and
  from `spanning_headline` (a full-width variant of `phase`, distinguished by width rather than
  color).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A document using a `subphase` heading shows that heading's background rendering
  visibly brighter than a `phase` heading's background, in 100% of generations.
- **SC-002**: A `subphase` heading renders at the same width/position as a standard `phase` heading
  (single-column), in 100% of generations.
- **SC-003**: A document with multiple `subphase` headings renders each one independently and
  correctly.
- **SC-004**: In print-friendly mode, `phase` and `subphase` always render as two distinguishable
  grayscale shades.
- **SC-005**: The same `subphase` placement renders with the identical background color across all
  languages of a given edition.
- **SC-006**: A maintainer can add, move, or remove a `subphase` heading using the same authoring
  process used for other content, without needing separate tooling or a code change.

## Assumptions

- This feature extends the content-authoring model established in `002-pdf-generation` (ordered
  content blocks rendered through a template) — `subphase` is one more kind of entry in that same
  ordered structure, authored the same way as `phase` (carrying a `title`).
- `subphase` is a **visible content block** (it has its own heading text), not a structural marker
  like the page-break or column-reset markers — it occupies a position in the reading flow and
  displays content.
- Distinguishability from `phase` is achieved purely through a brighter background color (per the
  user's explicit ask), not through width or shape — unlike `spanning_headline`, which is
  distinguished purely through width. This keeps each heading variant's distinguishing dimension
  orthogonal to the others' (`subsection` and `spanning_headline`).
- The exact color value is a design decision deferred to planning; this spec requires only that it be
  visibly brighter than `phase`'s background while staying in the same color family, and remain
  distinguishable from `phase` in print-friendly grayscale mode.
- This feature must remain compatible with the existing page-break (`005-page-breaks`) and
  column-reset (`006-column-reset`) features, and with print-friendly output (`011-print-friendly-pdf`),
  since a `subphase` heading may realistically be authored near either and must render correctly in
  both output modes.

## Dependencies

- Depends on `002-pdf-generation` for the ordered content-block model and PDF rendering pipeline that
  this feature adds a new block kind to.
- Must remain compatible with `005-page-breaks` and `006-column-reset`, whose pagination/column
  markers may be authored near a `subphase` heading.
- Must remain compatible with `011-print-friendly-pdf`'s grayscale color-resolution mechanism.
