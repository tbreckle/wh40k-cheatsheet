# Feature Specification: Python Quality Gates

**Feature Branch**: `001-python-quality-gates`

**Created**: 2026-08-13

**Status**: Draft

**Input**: User description: "Use ruff, pylint, bandit and ty for quality gates. enable a strong set of checkers to ensure up to date quality. support only python 3.12+"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Catch quality issues locally before pushing (Priority: P1)

A contributor working on the WH40K Cheatsheet runs a single command before pushing their change
and immediately sees every quality problem — style violations, likely bugs, security concerns, and
type errors — reported in one place, so they can fix them before opening a pull request.

**Why this priority**: Fast local feedback is what makes quality gates usable. If contributors can
only discover failures after a slow CI round-trip, they stop trusting the gate and route around it.
This story delivers the core value — a trustworthy, one-command quality check — and is a viable MVP
on its own.

**Independent Test**: Introduce a deliberate style violation, an obvious bug pattern, a hard-coded
credential, and a type error into a sample file, run the single quality command, and confirm all
four categories are reported with file and line locations and a non-zero exit code.

**Acceptance Scenarios**:

1. **Given** a clean codebase, **When** a contributor runs the quality-check command, **Then** all
   gates report success and the command exits successfully.
2. **Given** a file containing a style violation, a probable-bug pattern, a hard-coded secret, and a
   type error, **When** a contributor runs the quality-check command, **Then** each issue is
   reported with its category, file, and line, and the command exits with a failure status.
3. **Given** a reported issue, **When** the contributor reads the output, **Then** the message
   identifies which gate raised it and enough detail to locate and fix it.

---

### User Story 2 - Enforce quality gates automatically on every change (Priority: P2)

The project maintainer needs every pull request to be checked by the same gates automatically, so
that no change reaches the main branch without passing them, regardless of whether the contributor
ran the checks locally.

**Why this priority**: Local checks are opt-in; automated enforcement is what actually protects the
main branch. It builds directly on Story 1 by running the same gates in an unattended environment
and blocking merges on failure.

**Independent Test**: Open a change that fails at least one gate and confirm the automated check
reports failure and marks the change as not mergeable; open a passing change and confirm it is
reported as passing.

**Acceptance Scenarios**:

1. **Given** a change that violates one or more gates, **When** the automated check runs, **Then**
   it reports failure and the change is blocked from merging.
2. **Given** a change that passes all gates, **When** the automated check runs, **Then** it reports
   success and does not block merging.
3. **Given** the automated check and a local run of the same command, **When** both run on the same
   code, **Then** they produce the same pass/fail verdict.

---

### User Story 3 - Maintain a strong, current, Python 3.12+ rule set (Priority: P3)

A maintainer configures the gates once with a strong, explicitly enumerated set of checks targeting
Python 3.12+, so the project holds a high and consistent quality bar and can modernize the rule set
over time without ambiguity about what is enforced.

**Why this priority**: The value of the gates depends on how much they actually check. A weak or
undocumented rule set passes bad code silently. This story ensures the bar is deliberately high and
maintainable, but it depends on Stories 1 and 2 existing first.

**Independent Test**: Review the configuration and confirm it enables a broad, named set of checks
across style, correctness, security, and typing, and that the minimum supported Python version is
declared as 3.12; then confirm a construct valid only on older Python is flagged or that 3.12+
syntax is accepted.

**Acceptance Scenarios**:

1. **Given** the gate configuration, **When** a maintainer reviews it, **Then** the enabled checks
   are explicitly enumerated and cover style/formatting, correctness/lint, security, and typing.
2. **Given** the declared minimum Python version, **When** the gates run, **Then** they evaluate
   code against Python 3.12+ semantics and accept 3.12+ language features.
3. **Given** a new maintainer, **When** they read the configuration and its documentation, **Then**
   they can determine exactly which rules are enforced and how to adjust them.

---

### Edge Cases

- What happens when a rule reports a false positive that the contributor judges incorrect? There
  MUST be a documented, auditable way to suppress a specific finding inline with a justification,
  rather than disabling a whole gate.
- How does the system handle a finding that only one gate can catch (e.g., a security issue invisible
  to the style checker)? Each gate runs independently so its unique findings are never masked by
  another gate passing.
- What happens when the gates disagree or overlap (two tools flag the same line)? The output MUST
  remain understandable, attributing each finding to the gate that raised it.
- How does a contributor run the gates when only some tools are available? The command MUST report
  clearly which gate could not run rather than silently skipping it and reporting success.
- What happens on a large codebase — do local runs stay fast enough to be run routinely?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The project MUST provide a single command that runs all quality gates — style/format,
  correctness lint, security scan, and type check — and reports every finding in one run.
- **FR-002**: The quality command MUST exit with a failure status if any gate reports a violation,
  and a success status only when all gates pass.
- **FR-003**: Each finding MUST identify the gate that produced it, the file, and the line, in a
  form a contributor can act on directly.
- **FR-004**: Each gate MUST run independently so that findings unique to one gate are always
  surfaced regardless of other gates' results.
- **FR-005**: The same gates MUST run automatically on every proposed change to the main branch and
  MUST block the change from merging when any gate fails.
- **FR-006**: The local command and the automated enforcement MUST use the same configuration and
  produce the same pass/fail verdict for identical code.
- **FR-007**: The enabled set of checks MUST be strong and explicitly enumerated, covering style and
  formatting, correctness/likely-bug detection, security weaknesses, and type correctness.
- **FR-008**: The gates MUST target Python 3.12 as the minimum supported version, evaluating code
  against 3.12+ semantics and accepting 3.12+ language features; code targeting older versions is
  out of scope.
- **FR-009**: Contributors MUST be able to suppress an individual, justified false-positive finding
  in an auditable way (e.g., an inline annotation with a reason) without disabling an entire gate.
- **FR-010**: The gate configuration MUST be version-controlled and human-reviewable so that changes
  to what is enforced are diffable and auditable.
- **FR-011**: If a configured gate cannot execute (e.g., its tool is unavailable), the command MUST
  report that failure explicitly rather than reporting overall success.
- **FR-012**: The configuration and its documentation MUST make clear which rules are enforced and
  how a maintainer adjusts, adds, or removes them.

### Key Entities *(include if feature involves data)*

- **Quality Gate**: A single category of automated check (style/format, correctness lint, security,
  type). Has an enabled rule set, a pass/fail result, and a set of findings.
- **Finding**: A single reported issue. Attributes: originating gate, file, line, rule identifier,
  message, and severity.
- **Gate Configuration**: The version-controlled definition of which rules are enabled per gate and
  the minimum supported Python version, shared by local and automated runs.
- **Suppression**: An auditable, justified exception that silences one specific finding without
  weakening the gate for the rest of the codebase.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A contributor can run every quality gate with a single command and needs no more than
  one command to see all categories of findings.
- **SC-002**: 100% of changes merged to the main branch have passed all quality gates via automated
  enforcement.
- **SC-003**: For an intentionally seeded example containing a style violation, a likely bug, a
  hard-coded secret, and a type error, all four are reported in a single run.
- **SC-004**: A local quality run on the current codebase completes fast enough to be run routinely
  before every push (target: under 30 seconds on a typical developer machine).
- **SC-005**: The local command and the automated check agree on pass/fail for the same code in 100%
  of cases.
- **SC-006**: A maintainer can determine the complete set of enforced rules and the minimum Python
  version by reading version-controlled configuration, without inspecting tool internals.
- **SC-007**: A justified false positive can be suppressed for a single finding without reducing
  coverage elsewhere, and the suppression carries a recorded reason.

## Assumptions

- The gates are implemented with the tools named in the request: **ruff** (style/format and fast
  lint), **pylint** (deeper correctness lint), **bandit** (security scanning), and **ty** (type
  checking). These are treated as the concrete realization of the four gate categories.
- "A strong set of checkers" means enabling a broad, opinionated rule selection in each tool (well
  beyond defaults) rather than the minimal out-of-the-box set, tuned to avoid noise.
- The minimum supported runtime is Python 3.12; supporting older interpreters is explicitly out of
  scope, and tool target-version settings are set accordingly.
- The single local command may be provided via a task runner, script, or documented invocation; the
  exact mechanism is an implementation detail deferred to planning.
- Automated enforcement runs in the project's continuous-integration environment on pull requests to
  the main branch, consistent with the constitution's PR-only, all-gates-green workflow.
- `ty` is an evolving type checker; the configuration is expected to track its current recommended
  usage and be adjustable as it matures.

## Dependencies

- Depends on the project constitution's **Code Quality** principle and **Development Workflow &
  Quality Gates** section, which this feature operationalizes.
- Automated enforcement depends on a continuous-integration environment being available for the
  repository.
