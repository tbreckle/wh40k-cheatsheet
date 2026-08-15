# Feature Specification: PDF Generation from Templated Source Files

**Feature Branch**: `002-pdf-generation`

**Created**: 2026-08-13

**Status**: Draft

**Input**: User description: "build an application that reads data from files (containing config, strings, html) and create a pdf from it using a template. support multiple languages and editions (which is revisions)."

## Clarifications

### Session 2026-08-13

- Q: How is the set of editions, their supported languages, and their templates declared? → A: A single **project configuration file** declares all editions. It contains a mandatory `editions` structure; each edition has a **mandatory `template`** (template file name) and a **mandatory `languages`** object. `languages` is keyed by simple language code (`en`, `de`, `it`, …); each language entry MAY include an **optional `template`** that overrides the edition-level template for that language.

- Q: How are per-language string catalogs and HTML content fragments located for an edition? → A: By a fixed, documented **directory convention** keyed by edition id and language code (e.g. `editions/<edition-id>/<lang-code>/`); the project configuration file stays structure-only and does not declare content paths.

- Q: What file format should the project configuration file use? → A: **YAML** — nested, human-readable, comment-friendly, and diff-friendly, matching the constitution's human-reviewable-config requirement.

The declared configuration schema (YAML):

```yaml
editions:
  <edition-id>:
    template: <template-file-name>        # mandatory — default template for this edition
    languages:                            # mandatory — object of supported languages
      <lang-code>:                        # e.g. en, de, it — simple language codes
        template: <template-file-name>    # optional — overrides the edition template for this language
```

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate a cheatsheet PDF from source files (Priority: P1)

A cheatsheet maintainer has a set of source files — configuration describing what the document
contains, text strings, and HTML content fragments — plus a template that defines layout. They run
the generator and receive a finished PDF that composes those sources through the template.

**Why this priority**: This is the core value of the product. Without single-document generation,
nothing else matters; every other capability (languages, editions) is a variation on this. It is a
complete, demonstrable MVP on its own.

**Independent Test**: Provide a minimal but complete set of config, strings, and HTML files plus a
template, run the generator for one language and one edition, and confirm a valid PDF is produced
whose content matches the source strings and HTML laid out by the template.

**Acceptance Scenarios**:

1. **Given** a valid config, string set, HTML fragments, and a template, **When** the maintainer
   runs generation for one language and edition, **Then** a valid PDF file is produced that contains
   the specified content in the template's layout.
2. **Given** a source file is missing or malformed, **When** the maintainer runs generation, **Then**
   generation stops with a clear message naming the offending file and problem, and no partial or
   corrupt PDF is emitted.
3. **Given** the same unchanged sources and template, **When** generation is run twice, **Then** the
   two PDFs are equivalent in content (reproducible output).

---

### User Story 2 - Produce the document in multiple languages (Priority: P2)

The maintainer maintains the same document content in several languages via separate string sets,
and needs a localized PDF for each supported language without duplicating layout, configuration, or
HTML structure.

**Why this priority**: Multi-language support is a primary stated goal and a major share of the
product's audience value, but it builds directly on single-document generation (US1). It is
independently testable once US1 exists.

**Independent Test**: Provide string sets for two languages against one shared config/template/HTML
structure, run generation, and confirm one correctly localized PDF is produced per language with the
same layout and only the language-specific text differing.

**Acceptance Scenarios**:

1. **Given** string sets for multiple languages sharing one template and structure, **When** the
   maintainer requests generation for a specific language, **Then** the resulting PDF shows that
   language's text in the same layout as other languages.
2. **Given** multiple supported languages, **When** the maintainer requests generation for all of
   them, **Then** one PDF per language is produced in a single run.
3. **Given** a string is missing from one language's set, **When** that language is generated,
   **Then** the system reports which string is missing for which language rather than silently
   emitting a blank or wrong-language value.

---

### User Story 3 - Manage multiple editions (revisions) of the content (Priority: P3)

The maintainer keeps multiple editions — revisions of the content over time (e.g., as the underlying
game changes) — and needs to generate the PDF for a specific edition while keeping older editions
reproducible.

**Why this priority**: Editions add durability and traceability but are only meaningful once content
can be generated (US1) and localized (US2). It is the lowest of the three priorities while still
being a stated requirement.

**Independent Test**: Provide two editions of the source content, generate a chosen edition, and
confirm the PDF reflects that edition's content; then regenerate an earlier edition and confirm it
still produces that edition's content unchanged.

**Acceptance Scenarios**:

1. **Given** multiple editions of the source content, **When** the maintainer requests a specific
   edition, **Then** the produced PDF contains that edition's content and is identified with that
   edition.
2. **Given** an earlier edition, **When** it is regenerated later, **Then** its output content is
   unchanged from when that edition was current (past editions remain reproducible).
3. **Given** a language and an edition are both selected, **When** generation runs, **Then** the PDF
   corresponds to that specific language-and-edition combination.

---

### Edge Cases

- What happens when a requested language has no string set at all? Generation MUST fail with a clear
  message rather than fall back silently to another language.
- What happens when a requested edition does not exist? Generation MUST fail clearly and list the
  available editions.
- How are HTML fragments that reference missing images, styles, or broken markup handled? The system
  MUST report the problem rather than embedding broken content silently.
- What happens when a string exists in the catalog but is not referenced by any template/content, or
  a referenced key has no string? Unreferenced keys are ignored or reported; unresolved references
  MUST be reported (tie to US2 scenario 3).
- How does the system behave when the template and the content disagree (e.g., template expects a
  section the config does not provide)? It MUST report the mismatch rather than emit an incomplete
  document silently.
- What happens with content whose length overflows the template's layout (very long strings/tables)?
  Behavior MUST be defined and predictable (documented handling of overflow).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST read source inputs consisting of configuration (describing document
  structure/what to include), text strings, and HTML content fragments from files.
- **FR-002**: The system MUST apply a template that defines the document's layout and produce a PDF
  that composes the source inputs into that layout.
- **FR-003**: The system MUST produce a valid, openable PDF as its output artifact.
- **FR-004**: The system MUST support multiple languages, selecting the appropriate language-specific
  string set for a requested language while reusing shared configuration, template, and HTML
  structure.
- **FR-005**: The system MUST be able to generate one PDF per supported language in a single run when
  requested.
- **FR-006**: The system MUST support multiple editions (revisions of the content) and generate the
  PDF for a specifically requested edition.
- **FR-007**: The system MUST produce output for a specific language-and-edition combination when
  both are selected.
- **FR-008**: The system MUST validate its inputs before rendering and, on missing or malformed
  input, stop with a clear message identifying the file and the problem, emitting no partial or
  corrupt PDF.
- **FR-009**: The system MUST report unresolved content references — e.g., a referenced string key
  with no value in the selected language — identifying the missing item and the context (language,
  edition), rather than silently emitting blank or incorrect content.
- **FR-010**: The system MUST produce reproducible output: identical sources, template, language, and
  edition yield equivalent PDF content across runs.
- **FR-011**: Past editions MUST remain reproducible — regenerating an earlier edition yields that
  edition's content unchanged.
- **FR-012**: Each generated PDF MUST be identifiable by the language and edition it was produced
  for.
- **FR-013**: The set of supported languages and available editions MUST be discoverable by the
  maintainer (e.g., listable) so they know what can be generated.
- **FR-014**: The system MUST define and document predictable handling for content that overflows the
  template layout (long strings, large tables).
- **FR-015**: A single **project configuration file** MUST declare all editions and, for each
  edition, the set of supported languages and the template to use. This file is the authoritative
  source for what languages and editions can be generated (FR-013).
- **FR-016**: For each edition, the configuration MUST require a `template` (template file name) and a
  `languages` object; a configuration missing either mandatory key MUST fail validation with a clear
  message (per FR-008).
- **FR-017**: Each language entry under an edition MAY optionally specify its own `template`. Template
  resolution MUST use the language-level `template` when present and otherwise fall back to the
  edition-level `template`.
- **FR-018**: Language identifiers in the configuration MUST be simple language codes (e.g., `en`,
  `de`, `it`), and the requested language for generation MUST match one declared under the selected
  edition; an unknown language for that edition MUST fail clearly (per Edge Cases).
- **FR-019**: Per-language string catalogs and HTML content fragments MUST be resolved by a fixed,
  documented directory convention keyed by edition id and language code (e.g.,
  `editions/<edition-id>/<lang-code>/`). The project configuration file MUST remain structure-only
  and MUST NOT declare content file paths. Content expected by the convention but absent MUST be
  reported per FR-008/FR-009.

### Key Entities *(include if feature involves data)*

- **Project Configuration File**: The single authoritative file declaring all editions. Contains a
  mandatory `editions` structure; each edition holds a mandatory `template` (default template file
  name) and a mandatory `languages` object keyed by simple language code, where each language entry
  optionally overrides the template. Determines which language-and-edition combinations exist.
- **Source Configuration**: Per-edition content structure — which sections, content, and string keys
  make up the document. The blueprint the template and content are assembled around. (Distinct from
  the Project Configuration File, which declares editions/languages/templates rather than content.)
- **String Catalog**: The collection of translatable text strings for a given language, keyed by
  identifiers referenced from config/template/HTML. One catalog per language.
- **HTML Content Fragment**: A block of pre-authored rich content (markup) contributed into the
  document at a defined location.
- **Template**: The layout definition that arranges configuration, strings, and HTML fragments into
  the visual structure of the PDF. Shared across languages and (where unchanged) editions.
- **Language**: A supported locale identified by a simple language code (`en`, `de`, `it`, …),
  declared under an edition in the Project Configuration File with an optional per-language template
  override; selects which String Catalog is used and does not otherwise change layout.
- **Edition (Revision)**: A named revision of the content set representing its state at a point in
  time; declared in the Project Configuration File with a mandatory default template and its set of
  supported languages. Selecting an edition determines which version of the sources is rendered.
- **Generated Document**: The output PDF, associated with exactly one language and one edition.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A maintainer can generate a complete, valid PDF for one language and edition with a
  single generation action.
- **SC-002**: For any supported language, 100% of content strings defined for that language appear in
  the generated PDF, and any missing string is reported rather than silently omitted.
- **SC-003**: A maintainer can generate PDFs for all supported languages of a given edition in one
  run, producing exactly one PDF per language.
- **SC-004**: Regenerating any past edition produces content identical to its original generation in
  100% of cases (reproducibility).
- **SC-005**: Every malformed or missing input results in a clear, actionable error naming the file
  and problem, with zero corrupt or partial PDFs emitted.
- **SC-006**: A single document generation completes fast enough for routine iterative authoring
  (target: under 10 seconds per language-edition PDF for a typical cheatsheet on a standard
  developer machine).
- **SC-007**: A maintainer can list the available languages and editions without generating anything.

## Assumptions

- The primary user is a **cheatsheet maintainer** who runs the generator against version-controlled
  source files; the PDF's end readers are not users of this application directly.
- "Editions (which is revisions)" is interpreted as named revisions of the content set over time
  (e.g., tracking changes in the underlying game). Each edition is a self-contained version of the
  sources that can be rendered independently.
- The default output granularity is **one PDF per (language, edition) combination**; combined
  multi-language or multi-edition single PDFs are out of scope unless later requested.
- Source files (config, strings, HTML, templates) are stored in the project repository and are
  version-controlled and human-reviewable, consistent with the project constitution's data
  constraints.
- Generation is invoked as a build/authoring step (a command run by the maintainer), not an
  interactive end-user web action; the exact invocation mechanism is deferred to planning.
- "Config" describes document structure and inclusion; "strings" are the translatable text; "HTML"
  is richer pre-authored content — these three input kinds are distinct and combined by the template.
- The **project configuration file** is authored in **YAML** and is structure-only (editions,
  languages, templates); per-language strings and HTML are located by directory convention keyed by
  edition id and language code, not by paths in the config (see Clarifications 2026-08-13).
- Reproducibility means equivalent *content*; incidental metadata such as a generation timestamp is
  not required to be byte-identical unless a stricter definition is later requested.

## Dependencies

- Relies on the project constitution's **User Experience Consistency** principle (exact game
  vocabulary, consistent presentation) for how content is rendered, and its **Performance
  Requirements** for generation speed expectations.
- Assumes availability of authored source content (config, string catalogs, HTML fragments) and at
  least one template to render against.
