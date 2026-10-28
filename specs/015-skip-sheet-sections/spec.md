# Feature Specification: Skip Cheat Sheet Sections on Generation

**Feature Branch**: `015-skip-sheet-sections`

**Created**: 2026-09-15

**Status**: Draft

**Input**: User description: "New CLI args to skip parts of the generation. Ability to skip the for big blocks "Core Rules", "Core Abilities", "Datasheet Characteristics" and "Stratagems" generation."

## Clarifications

### Session 2026-09-15

- Q: Where is a sheet with omitted sections written - the same output file as the full sheet
  (replacing it), or a distinctly named file alongside it? → A: A distinctly named file alongside
  the full sheet, whose name encodes which sections were omitted (e.g. `en-no-stratagems.pdf` next to
  `en.pdf`), mirroring how the print-friendly variant already gets its own `-print` file. The full
  sheet is never replaced by a partial run, and each combination of omitted sections keeps its own
  file. (Planning later fixed the section id as `core-stratagems`, so the example file is
  `en-no-core-stratagems.pdf`.)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate a sheet without one section (Priority: P1)

A player who already knows one part of the rules by heart - typically the stratagems, or the
phase-by-phase core rules - wants a shorter printout without it, so the sheet on the table only
carries what they actually look up. They run the normal generate command and name the one section
to leave out.

**Why this priority**: This is the core value of the feature: fewer pages, less to scan at the
table. Omitting a single section is the smallest complete slice and is useful on its own.

**Independent Test**: Generate the 11th edition English sheet with "Core Stratagems" omitted. The
resulting PDF contains no stratagem content at all, every other section appears exactly as in the
full sheet, and there is no blank page where the stratagems used to be.

**Acceptance Scenarios**:

1. **Given** an edition whose sheet contains all four sections, **When** the sheet is generated
   with "Core Stratagems" omitted, **Then** no stratagem heading, stratagem card, or stratagem usage
   rules appear, and Core Rules, Core Abilities, and Datasheet Characteristics appear with the same
   content and order as in the full sheet.
2. **Given** the same edition, **When** the sheet is generated with "Core Rules" omitted, **Then**
   the sheet begins directly with Core Abilities, with no leading blank page or empty column.
3. **Given** any edition, **When** the sheet is generated without naming any section to omit,
   **Then** the output is identical to what generation produces today.

---

### User Story 2 - Omit several sections in one run (Priority: P2)

A player wants a compact quick-reference card, for example only the ability glossaries, or only the
stratagems. They name several sections to leave out in a single generate run instead of editing
content or post-processing the PDF.

**Why this priority**: Builds directly on Story 1 and enables the "reference card" use case, but a
single omission already delivers most of the value.

**Independent Test**: Generate a sheet with "Core Rules" and "Core Stratagems" omitted and confirm only
Core Abilities and Datasheet Characteristics remain.

**Acceptance Scenarios**:

1. **Given** an edition with all four sections, **When** "Core Rules" and "Core Stratagems" are omitted
   together, **Then** only Core Abilities and Datasheet Characteristics appear.
2. **Given** the same edition, **When** three sections are omitted, **Then** only the remaining
   section appears, with no blank pages.
3. **Given** any edition, **When** all four sections are omitted, **Then** generation fails with a
   clear message that nothing would be left to generate, and no output file is written or changed.

---

### User Story 3 - Consistent behavior across languages, editions, and variants (Priority: P3)

A maintainer generates several languages at once, or also requests the print-friendly variant, and
expects the same sections to be left out everywhere without repeating themselves per language.

**Why this priority**: Consistency matters for a multi-language product, but it refines Stories 1–2
rather than adding new capability.

**Independent Test**: Generate all languages of the 11th edition with "Datasheet Characteristics"
omitted and the print-friendly variant enabled; confirm the section is absent from every produced
PDF.

**Acceptance Scenarios**:

1. **Given** an edition with several languages, **When** all languages are generated in one run
   with a section omitted, **Then** that section is absent from every language's sheet.
2. **Given** the print-friendly variant is requested, **When** a section is omitted, **Then** the
   print-friendly sheet omits the same section as the standard sheet.
3. **Given** an edition that does not contain a section (the 10th edition sheet has no Datasheet
   Characteristics), **When** that section is named for omission, **Then** generation succeeds and
   the sheet is identical to generating it without that option, written under the standard file name.
4. **Given** a sheet generated with "Core Stratagems" omitted, **When** the full sheet already exists from
   an earlier run, **Then** the full sheet file is left unchanged and the partial sheet is written
   alongside it under its own name.

---

### Edge Cases

- A section name that is not one of the four recognized sections is rejected before anything is
  generated, and the error lists the valid section names.
- Naming the same section more than once behaves the same as naming it once.
- A section that is absent from the edition or language being generated is silently a no-op for that
  sheet (not an error), so one command can be reused across editions with different content.
- Page and column breaks that sit at a section boundary never leave a blank page or empty column
  behind when the adjacent section is omitted.
- Section titles are translated per language ("Stratagems" / "Gefechtsoptionen"), but the names used
  to omit a section are the same in every language.
- Omitting all four sections is an error, not an empty PDF.
- The order in which a user names sections to omit does not change the output file name; the same
  set of omitted sections always produces the same file.
- When the print-friendly variant is also requested, its file name carries both the omitted sections
  and the print-friendly marker, so it never collides with the standard partial sheet, the full
  sheet, or the full print-friendly sheet.
- If none of the named sections actually exist in a given sheet (so nothing is omitted from it), that
  sheet is written under its standard name, since its content is identical to the full sheet.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The generate command MUST accept an option to omit any of these four sheet sections:
  Core Rules, Core Abilities, Datasheet Characteristics, and Core Stratagems.
- **FR-002**: A user MUST be able to omit one or more sections in a single invocation.
- **FR-003**: When a section is omitted, ALL of its content MUST be excluded from the sheet,
  including its heading, its body content, and any section-specific notes (for example the rules for
  using stratagems that accompany the stratagem cards).
- **FR-004**: Sections that are not omitted MUST render with the same content, order, and appearance
  as in the full sheet.
- **FR-005**: Omitting a section MUST NOT introduce blank pages or empty columns.
- **FR-006**: When no section is named for omission, generated output MUST be identical to current
  behavior.
- **FR-007**: The names used to select sections MUST be the same for every language and edition,
  independent of how the section's title is translated on the sheet.
- **FR-008**: The omission MUST apply to every language generated in that run and to the
  print-friendly variant when it is requested.
- **FR-009**: Naming a section that the edition or language being generated does not contain MUST
  NOT be an error; that sheet is generated as if the option had not named it.
- **FR-010**: An unrecognized section name MUST cause generation to fail before any output is
  written, with a message listing the valid section names.
- **FR-011**: Omitting all four sections MUST cause generation to fail before any output is written,
  with a message explaining that nothing would remain. The same applies whenever the requested
  omissions would leave any sheet in the run with no content (e.g. omitting the three sections the
  10th edition sheet actually has).
- **FR-012**: A sheet generated with omitted sections MUST be written to its own file alongside the
  full sheet, never replacing the full sheet's file. The file name MUST identify which sections were
  actually omitted from that sheet (e.g. `en-no-core-stratagems.pdf`,
  `en-no-core-rules-core-stratagems.pdf`), listing them in the fixed sheet order Core Rules → Core
  Abilities → Datasheet Characteristics → Core Stratagems regardless of the order the user named them in.
  The print-friendly marker, when requested, MUST be applied in addition, so standard/print-friendly
  and full/partial files never collide. A sheet from which nothing was actually omitted (FR-009) MUST
  use the standard file name.
- **FR-013**: Every content block in every shipped edition and language MUST be attributable to
  exactly one of the four sections in a way that does not depend on translated titles, so that
  omission behaves identically across languages.
- **FR-014**: Release packaging MUST remain unaffected: published release assets always contain the
  full sheet with all sections.
- **FR-015**: The command's help output and the authoring/usage documentation MUST describe the
  option and list the valid section names.

### Key Entities

- **Sheet Section**: One of four named, language-independent parts of a cheat sheet - Core Rules,
  Core Abilities, Datasheet Characteristics, Core Stratagems. Each contains an ordered run of content
  blocks and has a translated display title. An edition or language may lack a section.
- **Section Omission Selection**: The set of section names a user asks to leave out for one
  generation run. Applies to every sheet produced by that run.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For every shipped edition and language, generating with any single section omitted
  yields a sheet containing none of that section's content and 100% of the other sections' content.
- **SC-002**: 0 generated sheets with omitted sections contain a blank page or empty column caused by
  the omission - verified per page for blank pages, and per column container for empty columns,
  across every combination of omitted sections.
- **SC-003**: Generating without naming any section produces output identical to the output before
  this feature, for all shipped content.
- **SC-004**: 100% of invalid selections (unknown section name, or all four sections) are rejected
  before any output file is written or changed.
- **SC-005**: A user can produce a sheet containing only Core Abilities and Datasheet Characteristics
  with a single command, without editing any content file.
- **SC-006**: 100% of content blocks in shipped content are attributable to exactly one section.
- **SC-007**: Generating a sheet with a section omitted never modifies an existing full sheet file for
  the same edition, revision, and language (0 changed bytes), and repeating the same omission always
  produces the same file name.

## Assumptions

- The four sections correspond to today's sheet layout: **Core Rules** is everything before the Core
  Abilities glossary (the five phases, actions, terrain, objectives, and related rules); **Core
  Abilities** is the abilities glossary; **Datasheet Characteristics** is the stat-abbreviation
  glossary; **Core Stratagems** is the stratagems heading, the stratagem cards, and the rules for using
  stratagems.
- Section boundaries are currently implicit in the content. Existing content files will need a
  one-time update so each block's section is stated explicitly rather than inferred from translated
  titles or page positions.
- The option applies to the generate command only. Release packaging always builds full sheets, so
  published releases never lack sections.
- Only omission is in scope. Reordering sections, selecting individual blocks, or defining new
  section names is out of scope.
- Omission names are fixed to these four sections; supporting additional sections later is a
  separate change.

## Dependencies

- `002-pdf-generation`: the generate command and ordered content-block model this feature filters.
- `005-page-breaks` and `006-column-reset`: break markers at section boundaries must not leave blank
  pages or columns when a neighbouring section is omitted.
- `007-spanning-headline` and `013-glossary-alphabetical-sort`: glossary and full-width headline
  behaviour of the sections that remain must be unchanged.
- `011-print-friendly-pdf`: the print-friendly variant must honour the same omission.
- `012-gitflow-release-pipeline`: release packaging must keep producing full sheets.
