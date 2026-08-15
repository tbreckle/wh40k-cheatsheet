# Feature Specification: Edition Revisions

**Feature Branch**: `003-edition-revisions`

**Created**: 2026-08-13

**Status**: Draft

**Input**: User description: "Each edition shall support revisions. Revisions are corrected editions. Revisions shall be date in YYYY-MM-DD-NN format (while NN is a number starting at 00 to 99, there are not more than 99 revisions a day). The latest revision shall be used except user requests a different revision."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate using the latest revision by default (Priority: P1)

A cheatsheet maintainer generates the document for an edition without naming a revision. The system
automatically selects that edition's most recent revision so the newest corrected content is
produced by default.

**Why this priority**: This is the everyday path — maintainers almost always want the newest
corrected content. Automatic "latest" selection is the core value of the feature and a complete MVP
on its own.

**Independent Test**: Provide an edition with two or more revisions, generate without specifying a
revision, and confirm the output is produced from the revision with the highest (most recent)
revision identifier.

**Acceptance Scenarios**:

1. **Given** an edition with revisions `2026-07-01-00` and `2026-08-01-00`, **When** the maintainer
   generates without naming a revision, **Then** the output is produced from `2026-08-01-00`.
2. **Given** an edition with multiple revisions on the same day (`2026-08-01-00`, `2026-08-01-01`),
   **When** the maintainer generates without naming a revision, **Then** the output is produced from
   `2026-08-01-01` (highest sequence that day).
3. **Given** an edition with exactly one revision, **When** the maintainer generates without naming a
   revision, **Then** that single revision is used.

---

### User Story 2 - Generate a specific requested revision (Priority: P2)

A maintainer needs to reproduce or inspect an earlier corrected version, so they explicitly request a
particular revision identifier and receive output from exactly that revision.

**Why this priority**: Reproducing a known past revision is essential for corrections, audits, and
comparisons, but it builds on the revision model established by US1.

**Independent Test**: Provide an edition with several revisions, request a specific older revision by
its identifier, and confirm the output reflects that exact revision rather than the latest.

**Acceptance Scenarios**:

1. **Given** an edition with revisions including `2026-07-01-00`, **When** the maintainer requests
   revision `2026-07-01-00`, **Then** the output is produced from that exact revision, not the
   latest.
2. **Given** a requested revision identifier that does not exist for the edition, **When** the
   maintainer generates, **Then** the system fails with a clear message and lists the available
   revisions.
3. **Given** a requested revision identifier that is not in `YYYY-MM-DD-NN` format, **When** the
   maintainer generates, **Then** the system rejects it with a clear message describing the required
   format.

---

### User Story 3 - Discover and validate an edition's revisions (Priority: P3)

A maintainer needs to see which revisions exist for an edition and be assured that revision
identifiers are well-formed and unambiguously ordered, so "latest" is always deterministic.

**Why this priority**: Discoverability and integrity make the default-and-override behavior
trustworthy, but they depend on revisions existing (US1) and being selectable (US2).

**Independent Test**: List an edition's revisions and confirm they appear in chronological order with
the latest identified; introduce a malformed revision identifier and confirm it is reported.

**Acceptance Scenarios**:

1. **Given** an edition with several revisions, **When** the maintainer lists revisions, **Then** all
   revisions are shown in chronological order (oldest → newest) with the latest clearly indicated.
2. **Given** an edition containing a malformed revision identifier, **When** revisions are read,
   **Then** the malformed identifier is reported rather than silently ignored or mis-ordered.
3. **Given** an edition with no revisions at all, **When** generation or listing is attempted,
   **Then** the system reports that the edition has no revisions rather than producing empty output.

---

### Edge Cases

- What happens when two revisions would share the same identifier (duplicate `YYYY-MM-DD-NN`)? This
  MUST be treated as an error — identifiers are unique per edition.
- What happens at the daily limit — a 101st revision on one day (NN would exceed `99`)? The format
  caps sequence at `99` (max 100 revisions per day, `00`–`99`); an identifier beyond this MUST be
  rejected as malformed.
- How is a revision date that is syntactically valid but not a real calendar date (e.g.,
  `2026-13-40-00`) handled? It MUST be rejected as malformed.
- What happens when a requested revision is well-formed and exists but its content is incomplete
  (e.g., missing a language)? The existing content-validation behavior applies (reported, not
  silently blanked) — revision selection does not bypass content checks.
- How does "latest" behave across editions — is it always scoped to a single edition? Yes; the latest
  revision is determined per edition, never across editions.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each edition MUST support one or more revisions, where a revision is a corrected version
  of that edition's content.
- **FR-002**: Every revision MUST be identified by an identifier of the form `YYYY-MM-DD-NN`, where
  `YYYY-MM-DD` is a valid calendar date and `NN` is a two-digit sequence from `00` to `99`.
- **FR-003**: The system MUST allow up to 100 revisions per day per edition (`NN` = `00`–`99`); an
  identifier whose sequence would exceed `99` MUST be rejected as invalid.
- **FR-004**: Revision identifiers MUST be unique within an edition; a duplicate identifier MUST be
  reported as an error.
- **FR-005**: The system MUST determine the "latest" revision of an edition as the one with the
  greatest identifier ordered by date and then by sequence (`NN`).
- **FR-006**: When the maintainer generates for an edition without specifying a revision, the system
  MUST use that edition's latest revision.
- **FR-007**: When the maintainer specifies a revision identifier, the system MUST use exactly that
  revision.
- **FR-008**: A requested revision that does not exist for the edition MUST cause a clear failure that
  lists the available revisions.
- **FR-009**: A requested or discovered revision identifier that does not conform to the
  `YYYY-MM-DD-NN` format (including invalid calendar dates or out-of-range sequences) MUST be
  reported with a message describing the required format.
- **FR-010**: The set of revisions available for an edition MUST be discoverable (listable) by the
  maintainer, presented in chronological order with the latest indicated.
- **FR-011**: An edition with no valid revisions MUST cause a clear report on generation or listing,
  rather than producing empty or default output.
- **FR-012**: Each generated output MUST be identifiable by the edition and the revision it was
  produced from.
- **FR-013**: "Latest" and all revision selection MUST be scoped to a single edition; revisions of
  one edition MUST NOT affect another edition's selection.

### Key Entities *(include if data involved)*

- **Revision**: A corrected version of an edition's content, identified by a `YYYY-MM-DD-NN`
  identifier. Belongs to exactly one edition. Ordered relative to other revisions of the same edition
  by date then sequence.
- **Revision Identifier**: The `YYYY-MM-DD-NN` value. Composed of a calendar date (`YYYY-MM-DD`) and a
  two-digit daily sequence (`NN`, `00`–`99`). Unique within an edition; totally ordered.
- **Edition**: An existing concept (from the PDF generation feature) that now owns an ordered set of
  one or more Revisions and has a well-defined "latest" revision.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: When no revision is specified, the system selects the edition's most recent revision in
  100% of cases, including when multiple revisions share a date.
- **SC-002**: When a specific existing revision is requested, the output is produced from exactly that
  revision in 100% of cases.
- **SC-003**: 100% of malformed revision identifiers (bad format, invalid date, sequence > 99) are
  rejected with a clear, actionable message; none are silently accepted or mis-ordered.
- **SC-004**: A request for a non-existent revision always fails with a message that includes the list
  of available revisions.
- **SC-005**: A maintainer can list an edition's revisions in correct chronological order with the
  latest clearly identified, without generating anything.
- **SC-006**: Every generated output can be traced to the exact edition and revision it came from.
- **SC-007**: Revision selection for one edition never changes the revision selected for any other
  edition.

## Assumptions

- This feature extends the existing **edition** concept from the PDF generation feature
  (`002-pdf-generation`); revisions are a sub-level of an edition, and generation, languages, and
  templates continue to work as already specified, now qualified by a selected revision.
- "Corrected editions" means a revision carries the same edition identity and purpose with refined or
  fixed content; it is not a new edition. Editions still represent larger content generations; a
  revision is a dated correction within one.
- Because `YYYY-MM-DD-NN` uses fixed-width, zero-padded, most-significant-first components, simple
  ascending ordering of the identifier equals chronological ordering; "latest" is the maximum.
- The default revision granularity follows the existing per-(edition, language) output model, now
  further qualified by revision — the maintainer's request may name an edition, optionally a
  language, and optionally a revision.
- How revisions are physically organized within the source layout (e.g., a per-revision directory
  under an edition) is an implementation concern deferred to planning; this spec defines only the
  identifier rules, selection behavior, and validation.
- Dates in revision identifiers are treated as opaque calendar dates for ordering and validation; no
  timezone handling is implied.

## Dependencies

- Depends on `002-pdf-generation` for the edition, language, template, and generation concepts that
  revisions qualify.
- Relies on the project constitution's traceability constraint (each output attributable to its
  source edition/version) — revisions make that attribution precise to a dated correction.
