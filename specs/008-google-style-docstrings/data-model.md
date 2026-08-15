# Phase 1 Data Model: Google-Style Docstrings Everywhere

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md) · Research: [research.md](./research.md)

This feature has no runtime data entities — it is a code-documentation and quality-gate-configuration
feature. The two conceptual "entities" below are the docstring content itself and the gate
configuration that enforces it; neither is a persisted or in-memory runtime structure.

---

## Entity: Docstring → attached to a `src/wh40k_cheatsheet` symbol

A Google-style docstring, attached to exactly one module, class, function, or method definition.

| Field | Type | Notes |
|-------|------|-------|
| `subject` | module \| class \| function \| method | What the docstring documents; determines which sections are required (FR-001/002/003). |
| `summary` | `str` | Required on every subject — a one-line description. |
| `extended` | `str`, optional | Optional additional paragraph(s) after the summary, before any sections. |
| `args` | ordered list of `(name, description)` | Required when the subject is a function/method with parameters other than `self`/`cls`. Must document every actual parameter and no others (FR-004; pylint `missing-param-doc`/`differing-param-doc`). |
| `returns` | `str`, present iff the subject returns non-`None` | Required whenever the function/method has an explicit `return <value>` (FR-003; pylint `missing-return-doc`, `accept-no-return-doc = false`). |
| `raises` | list of `(exception type, condition)` | Required for every exception type the subject deliberately raises via its own `raise` statement (FR-003; pylint `missing-raises-doc`, `accept-no-raise-doc = false`). |
| `attributes` | ordered list of `(name, description)`, class-subject only | Required when the class exposes public attributes (e.g. dataclass fields) (FR-002). |

**Validation rules**
- `args`/`raises`/`attributes` MUST be bidirectionally accurate: every entry corresponds to something
  real in the signature/body, and everything real in the signature/body that requires documentation
  has an entry (FR-004). Enforced by pylint's `docparams` extension (research.md §2).
- Type annotations already present on the signature satisfy any "type documented" requirement;
  `args`/`returns` descriptions are prose only, no redundant type repetition needed (research.md §2).
- Applies to every symbol in `src/wh40k_cheatsheet`, public and private (`_`-prefixed) alike,
  including explicit dunder methods; `tests/` is out of scope entirely (FR-006).

---

## Entity: Gate Configuration → `pyproject.toml` settings

The declarative configuration that turns the Docstring requirements above into an automatically
enforced, `poe check`-integrated gate (FR-005).

| Field | Location | Value | Purpose |
|-------|----------|-------|---------|
| Presence + format (public) | `[tool.ruff.lint] select` | includes `"D"` | Public-scope docstring presence and Google-style formatting (research.md §1). |
| Google convention | `[tool.ruff.lint.pydocstyle]` | `convention = "google"` | Selects the Google-compatible subset of `D`-rules. |
| Test exemption | `[tool.ruff.lint.per-file-ignores]` | `"tests/**"` gains `"D"` | Keeps `tests/` out of scope (FR-006). |
| Presence (public + private) | `[tool.pylint."messages control"] disable` | `missing-module-docstring`/`missing-class-docstring`/`missing-function-docstring` removed from the disabled list | Re-enables pylint's own presence checks, which — unlike ruff's — can cover private symbols once the regex below is overridden. |
| Private-symbol coverage | `[tool.pylint.basic]` | `no-docstring-rgx = "^$"` | Removes the default `^_` exemption so private symbols are checked too (research.md §1 — the key finding). |
| Accuracy checker | `[tool.pylint.main]` | `load-plugins` includes `"pylint.extensions.docparams"` | Enables Args/Returns/Raises-vs-signature checking; ships with pylint, no new dependency. |
| Accuracy strictness | `[tool.pylint.parameter_documentation]` | `accept-no-param-doc = false`, `accept-no-return-doc = false`, `accept-no-raise-doc = false`, `accept-no-yields-doc = false`, `default-docstring-type = "google"` | Turns off pylint's permissive "silently accept a totally missing section" defaults (research.md §2). |

**Validation rules**
- All of the above lives in the single `pyproject.toml`, consistent with `001-python-quality-gates`'
  "one central config file" approach — no new config file, no new tool.
- The gate self-test (plan.md's test structure) proves this configuration actually rejects a seeded
  violation and accepts a compliant fixture — config existing is not itself sufficient evidence.

---

## Relationships

```text
src/wh40k_cheatsheet/**/*.py
   └── each module/class/function/method definition
              │
              │ MUST have exactly one attached Docstring (see entity above)
              ▼
   Docstring { summary, [extended], [args], [returns], [raises], [attributes] }
              │
              │ verified against, on every `poe check` run
              ▼
   Gate Configuration (pyproject.toml: ruff D + pylint docparams, see entity above)
              │
              ├── PASS → merge eligible (Development Workflow & Quality Gates, constitution)
              └── FAIL → blocks merge, same as any existing lint/type/security finding
```

## State / flow

Stateless — docstrings are static source content; the gate re-evaluates them fresh on every
`poe check`/CI run. No persistence, no derived data, no runtime component.
