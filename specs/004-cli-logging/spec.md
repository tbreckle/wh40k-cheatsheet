# Feature Specification: CLI Progress Logging & Verbose Mode

**Feature Branch**: `004-cli-logging`

**Created**: 2026-08-14

**Status**: Draft

**Input**: User description: "Use logging to inform user on what's happening. Add a cli flag to enable verbose output."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See what the generator is doing while it runs (Priority: P1)

A maintainer runs `generate` and, while it executes, sees concise status messages for each major
step (loading configuration, resolving the edition/revision, resolving content, rendering, and
converting to PDF) instead of a silent wait followed by a final result line.

**Why this priority**: This is the core value of the feature — visibility into a multi-step,
multi-second operation so the maintainer knows the tool is working and roughly what it's doing. It
stands alone as a complete improvement even without the verbose flag.

**Independent Test**: Run `generate` for one edition/language and confirm status messages appear for
each pipeline stage, in order, before the final success line, without needing any extra flag.

**Acceptance Scenarios**:

1. **Given** a valid configuration and content, **When** the maintainer runs `generate`, **Then**
   they see an ordered status message for each major stage the run passes through, followed by the
   existing success output.
2. **Given** a run that generates multiple languages, **When** each language is processed, **Then**
   the status messages for one language's stages are not interleaved confusingly with another's —
   output remains readable in the order the work happens.
3. **Given** the `list` command, **When** it runs, **Then** its output remains as concise as today
   (no obligation for `list` to add step-by-step logging, since it does not perform multi-stage work).

---

### User Story 2 - Get detailed diagnostic output on demand (Priority: P2)

A maintainer investigating an issue or curious about exactly what the tool is doing adds a verbose
flag to the command and receives significantly more detail — resolved file paths, the template and
revision chosen, and other diagnostic context — without changing any other behavior or output
artifact.

**Why this priority**: Deeper diagnostics matter for troubleshooting but are secondary to the
baseline visibility of Story 1; most runs won't need this level of detail.

**Independent Test**: Run the same `generate` command once without and once with the verbose flag;
confirm the verbose run prints additional diagnostic detail (e.g., resolved paths and chosen
template/revision) while producing the identical PDF/HTML output as the non-verbose run.

**Acceptance Scenarios**:

1. **Given** a valid run, **When** the maintainer adds the verbose flag, **Then** additional
   diagnostic detail is printed beyond the default stage messages.
2. **Given** the verbose flag is not supplied, **When** the command runs, **Then** output matches the
   default (non-verbose) level described in User Story 1 — no diagnostic detail leaks through.
3. **Given** the same command run with and without the verbose flag, **When** comparing the generated
   PDF/HTML files, **Then** they are identical — verbosity affects console output only.

---

### User Story 3 - Errors are always visible regardless of verbosity (Priority: P3)

A maintainer whose run fails — at default or verbose level — sees the error clearly, so verbosity
never hides or buries a failure.

**Why this priority**: Correctness/safety net for the other two stories; lower priority because it
reinforces existing fail-loud behavior rather than adding new capability.

**Independent Test**: Trigger a known failure (e.g., unknown edition) once at default verbosity and
once with the verbose flag; confirm the error message is clearly visible and at least as informative
in both cases.

**Acceptance Scenarios**:

1. **Given** an error occurs during a run, **When** verbosity is at the default level, **Then** the
   error is clearly displayed and the run exits with a failure status, exactly as before this
   feature.
2. **Given** an error occurs during a run, **When** the verbose flag is set, **Then** the error is
   still clearly displayed (optionally with more diagnostic context) and the run exits with a failure
   status.
3. **Given** a large volume of verbose diagnostic output, **When** an error also occurs, **Then** the
   error remains distinguishable from routine diagnostic messages (not lost among them).

---

### Edge Cases

- What happens when verbose output is requested for a run that generates many languages at once?
  Output MUST stay ordered per-language and remain readable, not interleave unpredictably.
- What happens when the verbose flag is combined with an operation that has little to report (e.g.,
  `list`)? It MUST NOT error; it may simply have little or no additional detail to add.
- What happens if a stage completes near-instantly? Its status message MUST still appear (visibility
  is about clarity of steps, not just slow ones).
- Status/diagnostic messages MUST NOT include the content of generated cheat sheets (only metadata
  such as stage names, identifiers, and paths) — no risk of flooding output with rendered content.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST report a status message at each major stage of a `generate` run:
  configuration loaded, edition/revision resolved, content resolved, template rendered, PDF
  converted — at the default (non-verbose) output level.
- **FR-002**: Status messages MUST be emitted in the order the corresponding work happens and MUST
  clearly identify which stage they describe.
- **FR-003**: When generating multiple languages in one run, status messages MUST remain attributable
  to the specific language/stage they describe and MUST NOT be presented in a way that makes it
  ambiguous which run they belong to.
- **FR-004**: The CLI MUST provide a flag that enables a verbose output mode, off by default.
- **FR-005**: In verbose mode, the system MUST emit additional diagnostic detail beyond the default
  stage messages — at minimum, resolved file paths and the resolved template/revision/language for
  each generated document.
- **FR-006**: Enabling verbose mode MUST NOT alter the generated HTML/PDF output in any way; it MUST
  only affect what is printed to the console.
- **FR-007**: Error messages MUST be displayed clearly and MUST NOT be omitted, weakened, or hidden
  among other output at either verbosity level.
- **FR-008**: Error messages MUST remain visually/structurally distinguishable from routine
  status/diagnostic messages, especially when verbose mode produces a high volume of output.
- **FR-009**: The existing final result output (e.g., success confirmation, `list` output) MUST
  continue to appear at default verbosity — this feature adds visibility, it does not remove
  existing output.
- **FR-010**: Status and diagnostic messages MUST NOT include the substantive content of the cheat
  sheet being generated (e.g., rule text) — only operational metadata (stage names, identifiers,
  paths, timings).

### Key Entities *(include if feature involves data)*

- **Status Message**: A single line of operator-facing output describing a pipeline stage or
  diagnostic fact. Attributes: severity/level (routine status, diagnostic detail, error), the stage
  or operation it relates to, and human-readable text.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: While a `generate` run is in progress, a maintainer can tell which stage it is
  currently in without needing to enable any extra flag.
- **SC-002**: A maintainer can obtain materially more diagnostic detail (resolved paths,
  template/revision/language chosen) by adding a single flag, with no other change to how they invoke
  the tool.
- **SC-003**: Generated PDF/HTML output is byte-for-byte identical whether or not verbose mode is
  used, in 100% of cases.
- **SC-004**: 100% of run failures produce a clearly visible error message, regardless of verbosity
  level.
- **SC-005**: A maintainer generating multiple languages in one run can, from the output alone,
  correctly attribute each status message to the language/stage it belongs to.

## Assumptions

- This feature extends the existing `generate`/`list` CLI from `002-pdf-generation` /
  `003-edition-revisions`; it does not introduce new commands, only additional console output and one
  new flag on existing commands.
- "Logging" is interpreted as operator-facing console status/diagnostic output (progress visibility),
  not a requirement to persist logs to a file or integrate with an external log-aggregation system;
  those are out of scope unless later requested.
- Default (non-verbose) output is informative but concise — one line per major stage. Verbose output
  is additive detail, not a replacement of the default lines.
- The verbose flag applies per-invocation (a command-line flag), not a persistent configuration
  setting.
- "Errors always visible" builds on the fail-loud behavior already established in
  `002-pdf-generation` (FR-008) and `003-edition-revisions`; this feature does not change error
  content, only ensures it remains visible alongside the new status/diagnostic output.

## Dependencies

- Depends on the `generate`/`list` CLI commands introduced in `002-pdf-generation` and extended in
  `003-edition-revisions`; this feature adds observability to that existing surface rather than
  standing alone.
- Relates to the project constitution's implicit operability expectations for a maintainer-run tool;
  no specific principle mandates logging, but this feature improves the tool's usability during
  routine, iterative use.
