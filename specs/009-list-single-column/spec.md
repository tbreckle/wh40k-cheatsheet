# Feature Specification: List Single-Column (Full-Width) Flag

**Feature Branch**: `009-list-single-column`

**Created**: 2026-08-14

**Status**: Draft

**Input**: User description: "Enable list type to optionally be single column using an optional configuration flag."

## Clarifications

### Session 2026-08-14

- Q: What should the list block's new single-column flag actually change, given a `list` block
  already renders as one plain vertical list confined to whichever half of the two-column sheet it
  lands in? → A: Full-width single column — the flag makes the list span the complete width of both
  of the sheet's columns, one wide unbroken column instead of being confined to a narrow half-page
  column.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Give a specific list the full page width instead of a narrow column (Priority: P1)

A cheat-sheet author has a `list` block whose items read awkwardly when squeezed into one narrow
half-page column — long item text wraps onto several lines, or the list is meant to stand out as a
full-width summary. The author marks that specific list with an optional flag, and it renders across
the complete width of the page instead of being confined to one column.

**Why this priority**: This is the entire value of the feature — without it, an author has no way to
give a specific list more horizontal room; every list is stuck at half-page width regardless of
content shape.

**Independent Test**: Author a fixture with one flagged list and one standard list; render both and
confirm the flagged list's rendered width approximates the full page content width, while the
standard list's width approximates a single column.

**Acceptance Scenarios**:

1. **Given** a `list` block with the single-column flag enabled, **When** the document renders,
   **Then** the list's items span the complete width of both of the sheet's columns rather than
   being confined to one.
2. **Given** a `list` block without the flag (omitted or false), **When** the document renders,
   **Then** it behaves exactly as it did before this feature — confined to whichever single,
   half-width column it lands in.
3. **Given** a `list` block with the flag positioned between other content, **When** the document
   renders, **Then** content before it fills its column normally and content after it resumes
   correctly below the full-width list, with nothing lost, duplicated, or reordered.

---

### Edge Cases

- A flagged list is the very first or very last block in the document — renders correctly with no
  errors or unexpected blank space.
- A flagged list's items include nested sub-items — sub-items remain fully readable and correctly
  indented at the full page width.
- A flagged list coexists with a `page_break` or `column_reset` marker elsewhere in the document —
  each behaves exactly as documented for it, with no interference between the two features.
- A flagged list is long enough to overflow the current page — behaves the same as any other
  overflowing content (flows onto the next page); this feature does not change overflow handling.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A `list` content block MUST support an optional flag indicating it should render
  across the complete width of both of the sheet's columns, instead of being confined to one.
- **FR-002**: When the flag is absent or false, list rendering MUST remain identical to how it
  rendered before this feature — no behavior change for any existing content.
- **FR-003**: When the flag is enabled, every item (including nested sub-items) MUST remain fully
  readable, correctly ordered, and undamaged compared to the same list without the flag.
- **FR-004**: The full-width rendering MUST coexist correctly with existing `page_break` and
  `column_reset` markers, with no interference between the features.
- **FR-005**: The full-width layout MUST look and behave consistently with other full-width elements
  already used elsewhere in the document, so the document's visual language for "this spans the full
  page" stays uniform regardless of which content type uses it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A flagged list visibly spans the complete two-column content width, distinguishable
  from a standard, column-confined list purely by its width.
- **SC-002**: Content immediately before and after a flagged list always renders completely and in
  correct order — never cut off, duplicated, or misplaced.
- **SC-003**: Existing content that doesn't use the flag is completely unaffected by this feature —
  zero change to previously generated output.
- **SC-004**: Adding, moving, or removing the flag on a list requires only a content edit — no code
  change.

## Assumptions

- "Single column" means the list spans the full page width as one unbroken column, rather than
  being confined to a narrow half-page column within the sheet's existing two-column layout —
  resolved via the clarification above.
- The flag defaults to off/absent, so every list authored before this feature keeps rendering
  exactly as it does today.
- The flag affects only the outer column width the list occupies; nested sub-item indentation and
  bullet styling are unaffected.
- The flag's exact schema key/name is a planning-phase decision; it must be additive to the existing
  `list` block schema, changing no existing key's meaning.
