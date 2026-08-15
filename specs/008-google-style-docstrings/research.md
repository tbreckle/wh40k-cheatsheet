# Phase 0 Research: Google-Style Docstrings Everywhere

Feature: [spec.md](./spec.md)

The spec's Assumptions section already commits to reusing the existing quality-gate stack
(ruff/pylint) rather than adding a new tool. This research empirically verifies — by running the
actual installed ruff/pylint against scratch files, following this project's established
"verify against the installed tool" discipline (used for `005`–`007`'s CSS mechanisms) — exactly
which rules/options deliver FR-001–FR-007, since documentation-checker defaults are easy to get
subtly wrong (as several findings below show).

---

## 1. Enforcing docstring *presence* (FR-001/002/003)

**Decision**: Two complementary layers, both already-installed tools:

- **ruff's `D` (pydocstyle) rules**, with `[tool.ruff.lint.pydocstyle] convention = "google"`, added
  to `select`. Covers **public** modules/classes/functions/methods only (D100–D107) plus Google-style
  *formatting* rules (blank lines, summary punctuation, section formatting) that pylint does not
  check at all.
- **pylint's `missing-module-docstring` / `missing-class-docstring` / `missing-function-docstring`**
  (already present in the codebase's `disable` list from `001-python-quality-gates` — re-enable them),
  with `[tool.pylint.basic] no-docstring-rgx = "^$"` overriding the default `^_` regex.

**Rationale — the critical finding**: Empirically, **ruff's `D10x` rules only ever flag *public*
symbols** — verified by running `ruff check --select D` (google convention) against a scratch file
with a private class/method/function: zero findings on any of the three, only on their public
counterparts. This is pydocstyle's own rule design (the rule names literally say "public"), not a
configurable option — there is no ruff/pydocstyle setting to make D10x cover private symbols.
Since FR-006 requires private (`_`-prefixed) symbols in `src/` to be in scope too, ruff alone cannot
satisfy FR-006.

pylint's `missing-*-docstring` checks have the *same* default gap — verified the same way, zero
findings on private symbols — but unlike ruff, pylint exposes the responsible setting directly:
`no-docstring-rgx`, default `^_` (from `pylint --help`). Overriding it to `"^$"` (a regex matching
only the empty string, i.e. no real identifier) removes the exemption entirely; re-running the same
scratch file then correctly flags all six symbols (public and private class/method/function).
**Conclusion**: pylint (with the override) is the sole enforcer of *presence* across the full
FR-006 scope; ruff's `D` rules are kept for their formatting checks and as a redundant public-scope
signal, not as the presence enforcer.

**Current-state measurement** (informs plan Scale/Scope and task sizing): running the two configs
against the current `src/` tree:
- ruff `D` (public only): **55 findings** — 19 `D101` (class), 11 `D103` (function), 10 `D100`
  (module), 7 `D102` (method), 6 `D104` (package/`__init__.py`), 2 `D105` (magic method — google
  convention does **not** exempt dunders, contrary to a plausible assumption; verified empirically).
- pylint (public + private, `no-docstring-rgx="^$"`): **65 findings** — the extra 10 are private
  symbols ruff's public-only scope misses.

**Alternatives considered**:
- *`pydoclint`/`darglint` (dedicated docstring-signature checkers)*: more thorough for some edge
  cases, but the spec's Assumptions explicitly rule out introducing a new tool when the existing
  stack can do the job — confirmed below (§2) that pylint's bundled `docparams` extension covers
  FR-004 without a new dependency.
- *Rely on ruff `D` alone*: rejected — cannot cover private symbols (FR-006), a hard tool limitation,
  not a config gap.

---

## 2. Enforcing docstring *accuracy* — Args/Returns/Raises match the signature (FR-004)

**Decision**: Enable pylint's bundled `pylint.extensions.docparams` extension
(`[tool.pylint.main] load-plugins = ["pylint.extensions.docparams"]`), which ships with pylint
itself — no new dependency. Configure `[tool.pylint.parameter_documentation]` with
`accept-no-param-doc = false`, `accept-no-return-doc = false`, `accept-no-raise-doc = false`,
`accept-no-yields-doc = false`, and `default-docstring-type = "google"`.

**Rationale**: Verified empirically with a scratch module containing four functions: one correct,
one with a Google-style docstring that omits a real parameter, one that documents a parameter that
doesn't exist, and one that omits its `Returns:` section entirely.
- `missing-param-doc` (W9015) correctly fired for the omitted real parameter.
- `differing-param-doc` (W9017) correctly fired for the documented-but-nonexistent parameter.
- `missing-return-doc` (W9011) did **not** fire by default — pylint's docparams extension defaults
  `accept-no-return-doc` (and the equivalent `accept-no-param-doc`/`accept-no-raise-doc`/
  `accept-no-yields-doc`) to `True`, meaning a *totally* missing section is silently accepted unless
  explicitly turned off. Re-running with `--accept-no-return-doc=n` correctly flagged it. This is a
  real "default is permissive" trap the plan must configure around, not an oversight to work around
  differently.
- Docstring style is **auto-detected per docstring** from its structure (no `docstring-style`
  toggle needed) — pylint correctly parsed the Google-style scratch docstrings without any style hint;
  `default-docstring-type = "google"` is only the fallback when a docstring's style can't be guessed
  (e.g. malformed), set here for determinism.
- Functions with real Python type annotations (`-> int`, `x: int`) do **not** need redundant type
  mentions in `Args:`/`Returns:` prose — `missing-type-doc`/`missing-return-type-doc` did not fire
  against a fully-annotated-but-prose-only Google docstring in testing. This matches how this
  codebase is already written (heavy type annotations everywhere, per the constitution's Code
  Quality principle) and keeps docstrings from becoming type-annotation duplicates.

**Alternatives considered**:
- *Leave `accept-no-*-doc` at their permissive defaults*: rejected — this would silently satisfy
  FR-004 for "some params documented, all present" but do nothing for "no Returns section at all,"
  the more common omission risk in practice.

---

## 3. Magic methods (dunders) are not exempt (edge case for FR-003)

**Decision**: No special-case exemption; magic methods are documented like any other method once
`no-docstring-rgx` no longer matches them.

**Rationale**: Verified empirically against the codebase's two actual explicit dunder methods
(`RevisionId.__str__`, `RevisionId.__lt__` in `src/wh40k_cheatsheet/revision/identifier.py`) — with
`no-docstring-rgx = "^$"`, pylint flags both. (Auto-generated dunders from `@dataclass` decorators,
which is most of this codebase's magic-method surface, are never checked at all since they have no
source-level `def` for the checker to see.) This is a small, known, two-method addition during
implementation — not a gap requiring further config.

---

## 4. The one accepted tooling gap: a literally-empty `__init__.py`

**Decision**: Accept this as a documented, low-risk gap rather than adding tooling to close it.

**Rationale**: `src/wh40k_cheatsheet/__init__.py` is currently a genuinely empty (0-byte) file.
Verified empirically: pylint's `missing-module-docstring` does **not** flag a zero-byte file (its own
documented behavior: "Empty modules do not require a docstring"). The spec's edge cases require a
docstring here anyway (FR-001, "even if the module's own logic is a single import/`__all__` line").
Adding the docstring during implementation resolves this immediately; the residual gap is that if
someone later deleted that docstring line and the file became fully empty again, the gate would not
catch the regression. This is judged acceptable — full-file deletion-to-empty is an implausible
accidental edit, and closing it would require a new tool or a custom check, both of which the spec's
Assumptions rule out for an edge this narrow.

**Alternatives considered**:
- *Add a placeholder non-docstring statement to keep the file "non-empty" so the checker always
  applies*: rejected as unnecessary complexity for a regression path this unlikely.

---

## 5. Scope enforcement: `tests/` stays exempt (FR-006)

**Decision**: `[tool.ruff.lint.per-file-ignores] "tests/**"` gains `"D"` appended to its existing
`["S101", "PLR2004"]` list. No pylint change needed for scope, since `pylint` in this project's
`poe lint` task already only runs against `src` (`pylint src`, confirmed in `pyproject.toml`) — it
was never scanning `tests/` in the first place, so the private+public/tests-exempt split falls out
of the *existing* task wiring for pylint, and only needs one explicit line for ruff.

**Rationale**: Matches FR-006 exactly with minimal config surface — no new per-tool test-detection
logic, just the existing per-file-ignore mechanism already used for `S101`/`PLR2004`.

---

## Resolved unknowns summary

| Unknown | Resolution |
|---------|------------|
| Tool for docstring *presence*, public+private, `src/`-only | pylint `missing-*-docstring`, `no-docstring-rgx = "^$"` |
| Tool for docstring *format* (Google style structure) | ruff `D` rules, `pydocstyle.convention = "google"` |
| Tool for docstring *accuracy* (Args/Returns/Raises match signature) | pylint's bundled `pylint.extensions.docparams`, with all four `accept-no-*-doc` options set `false` |
| Docstring style auto-detection | Automatic per-docstring; `default-docstring-type = "google"` is fallback-only |
| Type annotations vs. docstring type mentions | Annotations satisfy type-doc checks; no redundant type text needed in prose |
| Magic methods | Not exempt; two real dunders in the codebase need docstrings added |
| Empty `__init__.py` | One accepted, documented tooling gap — closed by adding the docstring, not by new tooling |
| `tests/` exemption | One `per-file-ignores` line for ruff; pylint already scoped to `src` only |
| Current violation count (informs task sizing) | 55 ruff `D` findings (public-scope) / 65 pylint findings (public+private) across the current `src/` tree |

No open NEEDS CLARIFICATION items remain.
