# Feature Specification: Column Reset in Generated Output

**Feature Branch**: `006-column-reset`

**Created**: 2026-08-14

**Status**: Draft

**Input**: User description: "Required ability and type to reset the two column layout and start next content in left column."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Force the next content to start fresh in the left column (Priority: P1)

A maintainer authoring content wants a specific section to always begin at the top of the left
column of the two-column layout — regardless of where the preceding content happened to end (left
or right column) — so a loosely related section never straddles the column boundary or starts
part-way down the right column.

**Why this priority**: This is the entire value of the feature. Without it, maintainers have no way
to realign the two-column flow short of forcing an entire new page (the existing page-break marker
from `005-page-breaks`). It is a complete, demonstrable capability on its own.

**Independent Test**: Author content where a marker is inserted after enough material to have
reached the right column, generate the PDF, and confirm the content after the marker begins at the
top of the left column of wherever it lands, rather than continuing partway down a column.

**Acceptance Scenarios**:

1. **Given** content whose flow has reached the right column, **When** a column-reset marker is
   inserted at that point, **Then** the content immediately following the marker begins at the top of
   a left column.
2. **Given** content whose flow is still in the left column when the marker is inserted, **When** the
   PDF is generated, **Then** the content following the marker still begins at the top of a left
   column (the guarantee holds regardless of where the flow currently is).
3. **Given** the same content without any column-reset marker, **When** the PDF is generated,
   **Then** the content that would have followed the marker instead continues the normal column flow
   exactly as it did before this feature existed.

---

### User Story 2 - Reset without wasting a whole page (Priority: P2)

A maintainer wants to realign content to the left column without forcing everything after it onto a
brand-new page when there is still room left on the current page, so the document stays compact and
avoids needless blank space that a full page break would introduce for a minor realignment.

**Why this priority**: This is what distinguishes the feature from simply reusing the existing
page-break marker from `005-page-breaks`. It is secondary to Story 1's core capability but is the
reason this needs to be a distinct, new marker rather than an existing one.

**Independent Test**: Author content with a column-reset marker placed where a full page of room
remains; generate the PDF and confirm the reset content appears on the same page as the preceding
content whenever there is room for it, rather than always jumping to a new page.

**Acceptance Scenarios**:

1. **Given** ample room remains on the current page when a column-reset marker occurs, **When** the
   PDF is generated, **Then** the content following the marker appears on the same page, realigned to
   the left column, without an unnecessary blank area.
2. **Given** insufficient room remains on the current page for any further content, **When** a
   column-reset marker occurs, **Then** the following content naturally continues onto the next page
   (starting in its left column), the same as ordinary content overflow would behave.

---

### User Story 3 - Combine column resets with page breaks predictably (Priority: P3)

A maintainer authoring a longer document wants to use both the existing page-break marker
(`005-page-breaks`) and the new column-reset marker together, and expects their effects to combine
predictably rather than conflict or produce unexpected blank space.

**Why this priority**: Necessary for real documents that use both pagination tools together, but is
a refinement on top of Stories 1–2 rather than new core capability.

**Independent Test**: Author content using both marker types at different points and confirm each
produces its own correct, independent effect without interfering with the other.

**Acceptance Scenarios**:

1. **Given** a document containing both a page-break marker and a column-reset marker at different
   points, **When** the PDF is generated, **Then** each marker produces its own correct effect at its
   own location.
2. **Given** a column-reset marker placed immediately adjacent to a page-break marker with no content
   between them, **When** the PDF is generated, **Then** no blank page or blank column area is
   produced — the more specific transition (the page break) determines the outcome at that point.

---

### Edge Cases

- A column-reset marker at the very start of the document (before any content) MUST NOT alter output
  or create blank space — there is nothing to reset from.
- A column-reset marker at the very end of the document (after the last content) MUST NOT create
  trailing blank space.
- Multiple consecutive column-reset markers with no content between them MUST collapse to a single
  reset, not compound into extra blank space.
- A column-reset marker immediately adjacent to a page-break marker (in either order, with no content
  between them) MUST NOT produce a blank page or blank column region.
- There is no fixed limit on how many column-reset markers a document may contain.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide an author-usable marker, distinct from the existing page-break
  marker (`005-page-breaks`), that forces the content following it to begin in a left column of the
  two-column layout.
- **FR-002**: Content following a column-reset marker MUST begin in a left column regardless of
  whether the immediately preceding content ended in a left or right column.
- **FR-003**: A column-reset marker MUST NOT force a new page when sufficient room remains on the
  current page — the reset MUST be able to take effect within the same page.
- **FR-004**: Content preceding a column-reset marker MUST render exactly as it would without that
  marker present.
- **FR-005**: A column-reset marker at the very start of the document MUST NOT alter output or
  produce blank space.
- **FR-006**: A column-reset marker at the very end of the document MUST NOT produce trailing blank
  space.
- **FR-007**: Multiple consecutive column-reset markers with no content between them MUST produce a
  single reset, not compounding blank space.
- **FR-008**: A document MAY contain any number of column-reset markers; each MUST independently
  produce its own left-column realignment at its own location.
- **FR-009**: Column-reset markers and page-break markers MUST be usable together in the same
  document without interfering with each other's correctness; adjacency between the two MUST NOT
  produce blank pages or blank column regions.
- **FR-010**: Column-reset behavior MUST be identical across every supported language and edition of
  a document that shares the same marker placement.
- **FR-011**: Adding, removing, or repositioning a column-reset marker MUST be possible without
  altering the content itself (the text/sections around it).

### Key Entities *(include if feature involves data)*

- **Column Reset Point**: A maintainer-authored marker placed within a document's ordered content,
  indicating that everything following it MUST begin in a left column of the two-column layout. Has
  no content of its own; it is a structural instruction, not visible text. Distinct from a **Page
  Break Point** (`005-page-breaks`): a column reset does not force a new page, only a left-column
  realignment.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Content immediately following a column-reset marker begins in a left column in 100% of
  generations, regardless of where the preceding content ended.
- **SC-002**: For content authored with room remaining on the current page, a column-reset marker
  produces its effect on that same page rather than always forcing a new page.
- **SC-003**: A column-reset marker placed at the very start, very end, or consecutively with another
  never produces unexpected blank space.
- **SC-004**: A document combining column-reset and page-break markers produces the correct,
  independent effect for each marker in 100% of generations, with no blank pages or blank column
  regions at their adjacency points.
- **SC-005**: The same column-reset placement produces the equivalent left-column realignment across
  all languages of a given edition.

## Assumptions

- This feature extends the content-authoring model established in `002-pdf-generation` and used by
  `005-page-breaks` (ordered content blocks rendered through a template) — a column-reset point is
  one more kind of entry in that same ordered structure, authored the same way as a page-break point.
- "Left column" refers to the first column of the two-column layout already used throughout the
  generated document (`002-pdf-generation`'s two-column design) — this feature does not introduce a
  different column count or layout mode.
- A column reset is explicitly **lighter-weight** than a page break: it realigns the column flow but
  only forces a new page when the current page genuinely has no room left, matching ordinary content
  overflow behavior. This is what justifies it being a distinct capability from
  `005-page-breaks`'s page-break marker rather than a duplicate of it.
- This feature is about **explicit, maintainer-placed** markers, consistent with `005-page-breaks`'s
  scope decision — automatic realignment inference (e.g., always resetting before certain section
  types) is out of scope.
- Column-reset points are edition/revision content, so they are versioned and reviewed the same way
  as the rest of the cheat sheet's source content, consistent with the project constitution's
  traceability expectations.

## Dependencies

- Depends on `002-pdf-generation` for the ordered content-block model and PDF rendering pipeline that
  this feature adds a new block/marker kind to.
- Depends on `005-page-breaks` for the existing page-break marker this feature must coexist and
  combine correctly with (User Story 3, FR-009).
