# Contract: Google-Style Docstrings & Gate Configuration

Feature: [spec.md](../spec.md) · Plan: [plan.md](../plan.md) · Data model: [data-model.md](../data-model.md)

What every symbol in `src/wh40k_cheatsheet` must carry, and exactly what configuration makes that
automatically enforced.

---

## Authoring contract

### Module

```python
"""One-line summary of what this module provides.

Optional extended description.
"""
```

Every module — including `__init__.py` re-export files and the top-level, currently-empty
`wh40k_cheatsheet/__init__.py` — gets one, even if the rest of the file is a single import/`__all__`
line (FR-001).

### Class

```python
class Paths:
    """One-line summary of the class's purpose.

    Attributes:
        editions_root: What this attribute holds.
        templates_root: What this attribute holds.
    """
```

`Attributes:` is required whenever the class exposes public attributes (e.g. dataclass fields);
omit it for classes with no public attributes to document (FR-002).

### Function / method

```python
def resolve_content(editions_root: Path, edition_id: str, revision_id: str, language: str) -> dict[str, Any]:
    """One-line summary of what this function does.

    Args:
        editions_root: What this parameter is.
        edition_id: What this parameter is.
        revision_id: What this parameter is.
        language: What this parameter is.

    Returns:
        What the return value represents.

    Raises:
        ContentError: The condition under which this is raised.
    """
```

- `Args:` documents every parameter except `self`/`cls` — no more, no fewer (FR-004).
- `Returns:` is required whenever the function has an explicit `return <value>` (omit only for
  functions that always return `None`).
- `Raises:` documents every exception type the function's own `raise` statements produce.
- No type repetition in prose — the signature's type annotations already satisfy that; `Args:`/
  `Returns:` text describes *meaning*, not type.
- Applies to **public and private** (`_`-prefixed) symbols alike, including explicit dunder methods
  (e.g. `RevisionId.__str__`) — `tests/` is the only exemption (FR-006).

---

## Gate configuration contract

The following `pyproject.toml` keys are what make the authoring contract above automatically
enforced (FR-005), verified empirically in research.md:

| Section | Key | Value |
|---------|-----|-------|
| `[tool.ruff.lint]` | `select` | gains `"D"` |
| `[tool.ruff.lint.pydocstyle]` | `convention` | `"google"` |
| `[tool.ruff.lint.per-file-ignores]` | `"tests/**"` | gains `"D"` (exempts `tests/`) |
| `[tool.pylint."messages control"]` | `disable` | no longer includes `missing-module-docstring` / `missing-class-docstring` / `missing-function-docstring` |
| `[tool.pylint.main]` | `load-plugins` | includes `"pylint.extensions.docparams"` |
| `[tool.pylint.basic]` | `no-docstring-rgx` | `"^$"` (covers private symbols — default `"^_"` would exempt them) |
| `[tool.pylint.parameter_documentation]` | `accept-no-param-doc` | `false` |
| `[tool.pylint.parameter_documentation]` | `accept-no-return-doc` | `false` |
| `[tool.pylint.parameter_documentation]` | `accept-no-raise-doc` | `false` |
| `[tool.pylint.parameter_documentation]` | `accept-no-yields-doc` | `false` |
| `[tool.pylint.parameter_documentation]` | `default-docstring-type` | `"google"` |

---

## Behavioral contract

1. **Presence, public scope** (FR-001/002/003): `ruff check src` fails with `D100`–`D107` on any
   undocumented public module/class/function/method.
2. **Presence, private scope** (FR-006): `pylint src` fails with `missing-module-docstring` /
   `missing-class-docstring` / `missing-function-docstring` on any undocumented symbol, public or
   private.
3. **Accuracy** (FR-004): `pylint src` fails with `missing-param-doc`/`differing-param-doc` when a
   documented parameter doesn't match the real signature, and with `missing-return-doc`/
   `missing-raises-doc` when a `Returns:`/`Raises:` section is entirely absent from a function that
   needs one.
4. **`tests/` exemption** (FR-006): neither `ruff check tests` (for `D` codes) nor `pylint` (which
   only ever runs against `src`, per the existing `poe lint` task) flags anything in `tests/`.
5. **Compliant code passes clean** (SC-004): a fully Google-style-documented change produces zero
   docstring-related findings from `poe check`.
6. **Failure blocks merge exactly like existing gates** (FR-005): a docstring violation exits
   non-zero from `poe check`/`poe lint`, the same as an existing lint/type/security finding — no
   separate command, no separate CI step.

---

## Example output (illustrative)

```text
$ poe lint
src/wh40k_cheatsheet/pipeline.py:39:0: D103 Missing docstring in public function
src/wh40k_cheatsheet/pipeline.py:62:0: missing-return-doc (W9011)
```
