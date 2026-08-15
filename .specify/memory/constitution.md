<!--
Sync Impact Report
==================
Version change: (unversioned template) → 1.0.0
Rationale: Initial ratification. The prior file was the unpopulated scaffold; this is the
first concrete constitution, so MAJOR baseline 1.0.0 applies.

Modified principles:
  - [PRINCIPLE_1_NAME] → I. Code Quality
  - [PRINCIPLE_2_NAME] → II. Testing Standards (NON-NEGOTIABLE)
  - [PRINCIPLE_3_NAME] → III. User Experience Consistency
  - [PRINCIPLE_4_NAME] → IV. Performance Requirements
  - [PRINCIPLE_5_NAME] → (removed; user requested four principles)

Added sections:
  - Additional Constraints & Standards (was [SECTION_2_NAME])
  - Development Workflow & Quality Gates (was [SECTION_3_NAME])

Removed sections:
  - Fifth principle slot from the template (intentional; four principles requested)

Follow-up TODOs:
  - None. All placeholders resolved.
-->

# WH40K Cheatsheet Constitution

## Core Principles

### I. Code Quality

Code MUST be readable, self-consistent, and reviewable before it is merged.

- Every change MUST pass automated linting and formatting; style is enforced by tooling, not
  debated in review. No merge with failing lint or formatter checks.
- Static type checking MUST pass with zero new errors. Public functions and module boundaries
  MUST carry type annotations.
- Functions MUST have a single clear responsibility. Duplicated logic MUST be factored into a
  shared unit rather than copied.
- Names MUST describe intent. Dead code, commented-out blocks, and unused dependencies MUST be
  removed, not accumulated.
- Every merge to the main branch MUST be reviewed by at least one person other than the author.

**Rationale:** A cheatsheet's value is trust in its correctness; unreadable or untyped code hides
defects that surface as wrong rules at the table. Enforcing quality by tooling keeps review focused
on logic and intent instead of style.

### II. Testing Standards (NON-NEGOTIABLE)

Behavior MUST be proven by automated tests, and tests MUST exist before the behavior is trusted.

- Every bug fix MUST add a regression test that fails before the fix and passes after.
- Every new feature or data rule MUST ship with tests covering its expected behavior and at least
  one boundary or failure case.
- The test suite MUST run in CI on every change; a red suite MUST block merge. There are no
  skipped, disabled, or "flaky-tolerated" tests on the main branch.
- Game data (unit stats, rules, points) MUST be validated by automated checks against its schema so
  malformed or contradictory entries fail the build, not the user.

**Rationale:** A rules reference that is wrong is worse than none. Tests are the only durable
guarantee that displayed data and computed results match the source rules, and that fixes stay
fixed.

### III. User Experience Consistency

The interface MUST behave predictably and identically across equivalent situations.

- Shared UI patterns (navigation, search, tables, terminology) MUST be reused; the same action
  MUST look and behave the same everywhere it appears.
- Terminology and data presentation MUST match the source game vocabulary exactly — no invented
  abbreviations or reworded rules.
- The application MUST be usable on mobile and desktop viewports, since cheatsheets are consulted
  at the table. Core content MUST remain reachable without horizontal scrolling.
- Every interactive element MUST have a visible state for loading, empty, and error conditions;
  the user is never left with an ambiguous or blank screen.
- The interface MUST meet WCAG 2.1 AA for contrast, keyboard navigation, and labeling.

**Rationale:** During a game, users scan quickly under time pressure. Consistency and accessibility
turn the tool into muscle memory; surprises cost the user the game turn they were trying to save.

### IV. Performance Requirements

The application MUST feel instant for lookup-style use.

- Lookups, searches, and filters MUST return results in under 200ms on a mid-range device for the
  full dataset; perceived interaction latency MUST stay under 100ms.
- Initial page load MUST reach interactive state in under 2 seconds on a typical mobile connection.
- Core reference content MUST be usable offline or on flaky connections once loaded; a dropped
  network MUST NOT block reading already-loaded data.
- Performance-sensitive paths MUST have a measurable budget (bundle size, query time) checked in
  CI; regressions past budget MUST block merge until justified or fixed.

**Rationale:** The tool competes with flipping through a physical book. If it is slower than paper,
it will not be used. Explicit budgets keep speed from silently eroding as content grows.

## Additional Constraints & Standards

- Game data MUST be stored in a structured, version-controlled, human-reviewable format so rules
  changes are diffable and auditable.
- Data sourcing MUST be traceable: each rule or stat block MUST be attributable to its source
  edition/version so it can be verified and updated when the game changes.
- Dependencies MUST be pinned and periodically reviewed; a new runtime dependency MUST be justified
  against the cost of adding it.
- No secrets, personal data, or credentials in the repository or client bundle.

## Development Workflow & Quality Gates

- All work MUST land through pull requests; direct pushes to the main branch are prohibited.
- A pull request MUST pass every automated gate — lint, format, type check, tests, and performance
  budgets — before it is eligible to merge.
- Reviewers MUST verify the change against these principles, not only that code "works". A reviewer
  MUST block a change that violates a principle unless an explicit, documented exception is granted.
- Any deviation from a principle MUST be recorded in the pull request with its justification, so
  complexity and exceptions are visible rather than silent.

## Governance

This constitution supersedes ad-hoc practices and conventions. When a rule here conflicts with
habit or convenience, this document wins.

- **Amendments** MUST be proposed via pull request that states the change, its rationale, and its
  impact on existing work. Amendments take effect only once merged.
- **Versioning** follows semantic versioning of governance:
  - MAJOR: a principle is removed or redefined in a backward-incompatible way.
  - MINOR: a new principle or section is added, or guidance is materially expanded.
  - PATCH: clarifications, wording, and non-semantic refinements.
- **Compliance review:** every pull request review MUST confirm adherence to these principles.
  Exceptions MUST be documented in the pull request and are granted per-change, never blanket.
- Runtime development guidance and agent instructions live alongside the code; where they conflict
  with this constitution, the constitution governs.

**Version**: 1.0.0 | **Ratified**: 2026-08-13 | **Last Amended**: 2026-08-13
