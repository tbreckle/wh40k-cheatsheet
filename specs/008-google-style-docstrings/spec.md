# Feature Specification: Google-Style Docstrings Everywhere

**Feature Branch**: `008-google-style-docstrings`

**Created**: 2026-08-14

**Status**: Draft

**Input**: User description: "Use pydoc documentation with Google style everywhere."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand any module, class, or function without reading its implementation (Priority: P1)

A maintainer or contributor opens any source file, hovers in their IDE, or runs `pydoc <module>` /
`help(<object>)` in a REPL, and sees a clear, standard-format docstring explaining what the symbol
does, its parameters, its return value, and any exceptions it raises — without having to read the
implementation first.

**Why this priority**: This is the core value proposition — discoverability and comprehension
without spelunking through code. Every other story builds on docstrings actually existing and
following one consistent, tool-readable format.

**Independent Test**: Run `python -m pydoc wh40k_cheatsheet.<any module>` (or `help()` in a REPL) on
any module in the package and confirm every public class/function shows a non-empty, Google-style
docstring including a summary, `Args:`, and `Returns:` (where applicable).

**Acceptance Scenarios**:

1. **Given** any public function in `src/wh40k_cheatsheet`, **When** a contributor inspects it via
   `help()`/pydoc/an IDE tooltip, **Then** they see a one-line summary, an `Args:` section listing
   every parameter and its purpose, and a `Returns:` section describing the return value (when the
   function returns something other than `None`).
2. **Given** any public class, **When** inspected the same way, **Then** its docstring explains the
   class's purpose and, if it exposes public attributes, documents them under an `Attributes:`
   section.
3. **Given** any module file, **When** opened or inspected via pydoc, **Then** it has a module-level
   docstring summarizing its purpose within the package.

---

### User Story 2 - Enforcement prevents undocumented code from being merged (Priority: P2)

A contributor adds a new public function, class, or module without a docstring, or with a docstring
that doesn't follow Google style; the project's existing quality gates (from
`001-python-quality-gates`) catch this automatically and fail the check, the same way they already
catch formatting/lint/type issues today.

**Why this priority**: Without automated enforcement, documentation coverage decays the moment it's
not actively watched — this is what makes Story 1's guarantee durable rather than a one-time cleanup.

**Independent Test**: Add a new public function without a docstring (or with a non-Google-style
docstring) on a scratch branch and confirm the quality-gate run fails specifically on the
missing/malformed docstring, reporting the exact symbol and file/line.

**Acceptance Scenarios**:

1. **Given** a new public function with no docstring, **When** the quality gates run, **Then** the
   run fails and reports the missing docstring's location.
2. **Given** a docstring that omits a parameter the function actually takes, **When** the quality
   gates run, **Then** the run fails and identifies the mismatch.
3. **Given** a fully-documented, Google-style-compliant change, **When** the quality gates run,
   **Then** they pass with no docstring-related findings.

---

### User Story 3 - Existing code is retrofitted, not just new code (Priority: P3)

All code that already exists in the package today gets Google-style docstrings, so the guarantee in
Story 1 is true immediately upon shipping this feature, not just for code written afterward.

**Why this priority**: Enforcement alone (Story 2) only protects new/changed code; the current,
undocumented codebase needs a one-time pass so the "everywhere" promise is true from day one.

**Independent Test**: Run the enforcement mechanism from Story 2 against the repository immediately
after this feature is implemented and confirm zero missing/malformed docstring findings.

**Acceptance Scenarios**:

1. **Given** the state of the repository after this feature is implemented, **When** the docstring
   quality gate runs across the covered source tree, **Then** it reports zero violations.

---

### Edge Cases

- What happens for a module that only re-exports symbols from submodules (e.g. `__init__.py`
  files)? It still needs a module-level docstring, even if the module's own logic is a single
  import/`__all__` line.
- What happens for a very small, self-explanatory function (e.g. a one-line `@property`)? It still
  needs at minimum a one-line summary docstring; Google style doesn't require an `Args:`/`Returns:`
  section when there's nothing non-trivial to document (e.g. a parameterless property).
- What happens for private (underscore-prefixed) helper functions? They are in scope (FR-006) —
  same Google-style requirement as public symbols, since they're still read by maintainers.
- What happens for the test suite (`tests/`)? Out of scope (FR-006) — test functions keep relying on
  descriptive names instead of docstrings.
- What happens to existing inline code comments (e.g. ones explaining a non-obvious workaround)?
  They stay as ordinary code comments — this feature governs docstrings (module/class/function-level
  documentation) only, not inline comments.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Every public module in the covered source tree MUST have a module-level docstring
  summarizing its purpose.
- **FR-002**: Every public class MUST have a docstring describing its purpose, formatted per Google
  style (summary line, optional extended description, an `Attributes:` section when the class
  exposes public attributes).
- **FR-003**: Every public function and method MUST have a docstring formatted per Google style: a
  one-line summary, an `Args:` section documenting every parameter (excluding `self`/`cls`), a
  `Returns:` section describing the return value when the function returns something other than
  `None`, and a `Raises:` section for any exception the function deliberately raises as part of its
  documented contract.
- **FR-004**: Docstring content MUST accurately describe the current signature — every documented
  parameter must exist, every actual parameter must be documented, and the documented return
  description must match what the function actually returns.
- **FR-005**: The project's quality gates MUST automatically verify docstring presence and
  Google-style formatting, and MUST fail the same way existing lint/type/security checks already do
  when a violation is found.
- **FR-006**: This requirement applies to every module, class, function, and method in
  `src/wh40k_cheatsheet` — public and private (`_`-prefixed) alike. The `tests/` suite is exempt: test
  functions rely on long, self-documenting names instead of docstrings, consistent with existing
  project convention.
- **FR-007**: All code that exists in the repository as of this feature's implementation MUST be
  retrofitted with compliant docstrings — the enforcement gate MUST pass with zero violations
  immediately upon completion, not only for future changes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of public modules, classes, functions, and methods in the covered source tree have
  a docstring, verified automatically rather than by manual audit.
- **SC-002**: A maintainer unfamiliar with a given file can determine what any public function does,
  what arguments it takes, and what it returns, using only `pydoc`/`help()`/an IDE tooltip — without
  opening the implementation.
- **SC-003**: A change that adds an undocumented or incorrectly-documented public symbol is
  automatically rejected by the existing quality-gate workflow, with zero manual review needed to
  catch the omission.
- **SC-004**: Zero docstring-related findings when the quality gates are run against the repository
  immediately after this feature ships.

## Assumptions

- "Google style" refers to the docstring format documented in the Google Python Style Guide (summary
  line; `Args:`, `Returns:`, `Raises:`, `Attributes:` sections as applicable) — the same convention
  already recognized by common tooling (e.g. `pydocstyle`'s `google` convention, ruff's `D` rules,
  Sphinx's Napoleon extension), not a project-specific variant.
- Enforcement is added to the existing quality-gate stack from `001-python-quality-gates`
  (ruff/pylint, configured centrally in `pyproject.toml`) rather than introducing a new, separate
  tool — consistent with that feature's approach. The specific rule set is a planning-phase decision.
- This feature governs docstrings only, not inline code comments — the project's existing
  "comment only when the why is non-obvious" convention for inline comments is unaffected.
- Dataclass fields and simple `@property` accessors need at minimum a one-line docstring summary; a
  full `Args:`/`Returns:` breakdown is only required when the symbol has non-trivial parameters or
  return semantics.
