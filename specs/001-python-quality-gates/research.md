# Phase 0 Research: Python Quality Gates

Feature: [spec.md](./spec.md) · Plan: [plan.md](./plan.md)

This document resolves the technical unknowns behind an "ultra modern Python 3.12+" quality-gate
stack with all configuration centralized in `pyproject.toml`.

---

## 1. Package & environment manager

**Decision**: Use **uv** (Astral) as the package/environment manager, with a committed `uv.lock`.

**Rationale**: uv is the current fast, all-in-one resolver/installer/venv manager and the de-facto
"ultra modern" choice. It reads standard `pyproject.toml` PEP 621 metadata, produces a reproducible
lockfile (satisfying the constitution's "dependencies MUST be pinned"), and provides `uv run` so
contributors and CI execute tools in an identical, isolated environment without manual venv steps.

**Alternatives considered**:
- *Poetry*: mature but slower, uses a partially non-standard metadata history; heavier than needed.
- *pip + venv + pip-tools*: works but more moving parts and no single ergonomic runner.
- *PDM/Hatch environments*: capable, but uv has become the ecosystem default for speed and DX.

---

## 2. Build backend & packaging metadata

**Decision**: PEP 621 `[project]` metadata with **hatchling** as the `[build-system]` backend;
`requires-python = ">=3.12"`; src layout package `wh40k_cheatsheet`.

**Rationale**: hatchling is a modern, standards-compliant, low-config build backend that plays well
with uv and the src layout. Declaring `requires-python = ">=3.12"` enforces the Python floor at
install time (FR-008) and is the single source of truth other tools inherit their target from.

**Alternatives considered**:
- *uv_build*: newer uv-native backend; viable but hatchling is more broadly proven today.
- *setuptools*: works but more boilerplate and legacy baggage for a greenfield project.
- *flit-core*: minimal but less flexible for future packaging needs.

---

## 3. Single aggregate command / task runner

**Decision**: Define tasks in **`[tool.poe.tasks]`** (poethepoet), exposing `poe check` that runs
every gate and a `poe fix` for auto-fixable formatting/lint. CI runs the same `poe check`.

**Rationale**: Keeps the aggregate-command definition *inside `pyproject.toml`* (the user's explicit
requirement — no Makefile/justfile), satisfies FR-001/FR-006 (one command, identical local vs CI),
and can be run via `uv run poe check`. poe runs each gate as an independent sub-task so a failure in
one still lets the others report (FR-004/FR-011) while yielding an overall non-zero exit (FR-002).

**Alternatives considered**:
- *Makefile / justfile*: rejected — configuration would live outside `pyproject.toml`.
- *nox / tox*: powerful for multi-env matrices but heavier than needed and config-in-Python/ini.
- *Plain shell script*: not cross-platform (Windows) and lives outside `pyproject.toml`.

---

## 4. Gate 1 — Style & format + fast lint: ruff

**Decision**: **ruff** provides both formatting (`ruff format`) and fast linting (`ruff check`),
configured under `[tool.ruff]` with `target-version = "py312"`, **`line-length = 120`**, and a broad
`lint.select`. The 120 setting drives both the formatter's wrap width and the `E501` line-length
lint, so format and lint agree on one number.

**Rationale**: ruff is the modern standard, replacing black/isort/flake8/pyupgrade/pydocstyle at
high speed. A strong selection enables (among others): `E`,`W` (pycodestyle), `F` (pyflakes),
`I` (isort), `N` (pep8-naming), `UP` (pyupgrade — keeps code on 3.12+ idioms), `B` (bugbear),
`A` (builtins), `C4` (comprehensions), `SIM` (simplify), `PTH` (pathlib), `RUF` (ruff-specific),
`S` (flake8-bandit subset), `PL` (pylint parity), `TID`, `TCH`, `PERF`, `FURB`, `DTZ`, `RET`,
`ARG`, `ERA`, `D` (docstrings). Auto-fix handles the mechanical subset.

**Alternatives considered**:
- *black + isort + flake8 + plugins*: the pre-ruff stack; slower, many tools, more config files.
- *ruff defaults only*: rejected — spec requires an explicitly strong, enumerated rule set (FR-007).

---

## 5. Gate 2 — Deep correctness lint: pylint

**Decision**: **pylint** configured under `[tool.pylint]` in `pyproject.toml`, run as its own gate
with a high-signal rule set and **`max-line-length = 120`** (matching ruff); disable only the checks
that ruff already owns to avoid double-noise.

**Rationale**: pylint catches design/correctness smells ruff does not (e.g., inference-based
no-member, too-many-*, cyclic imports, some type-inference warnings). Running it as a distinct gate
honors FR-004 (independent gates). Overlap with ruff is reduced by disabling formatting/style
categories in pylint so each gate has a clear lane while keeping pylint's unique value.

**Alternatives considered**:
- *Skip pylint, rely on ruff's `PL` rules*: ruff implements only a subset; pylint's full inference
  engine adds real coverage the spec's "strong set" intends.
- *pylint for everything*: too slow and noisy as the sole linter; ruff is the fast front line.

---

## 6. Gate 3 — Security: bandit

**Decision**: **bandit** configured under `[tool.bandit]`, scanning `src/` for security weaknesses;
tests excluded from some checks via bandit's test-path handling.

**Rationale**: bandit is the standard SAST tool for Python (hard-coded secrets, weak crypto, shell
injection, unsafe deserialization). It catches the "hard-coded secret" class in SC-003 that lint and
typing miss, giving the security gate independent value (FR-004). Config in `pyproject.toml` keeps
the single-config-file rule.

**Alternatives considered**:
- *ruff `S` rules only*: ruff embeds a bandit subset, but full bandit has broader, maintained
  coverage and severity/confidence tuning; running both is complementary, not redundant.
- *semgrep*: more powerful but heavier and rule-hosting adds external dependency/complexity.

---

## 7. Gate 4 — Type checking: ty

**Decision**: **ty** (Astral's type checker) configured under `[tool.ty]`, targeting Python 3.12,
run as the typing gate over `src/`.

**Rationale**: ty is the "ultra modern", extremely fast type checker aligned with the ruff/uv
toolchain. It provides the type-correctness gate (SC-003 type-error detection). Because ty is young
and evolving, the configuration is kept explicit and is expected to track its recommended settings;
this is called out as a maintenance assumption in the spec.

**Alternatives considered**:
- *mypy*: the incumbent, most mature; a reasonable fallback if ty lacks a needed check. Rejected as
  the primary per the user's "ultra modern stack" directive, but noted as the escape hatch.
- *pyright*: fast and thorough but Node-based, outside the pure-Python/Astral stack the user wants.

**Risk note**: If ty cannot yet enforce a required check or blocks CI due to pre-release
instability, the documented mitigation is to pin a known-good ty version in `uv.lock` and, if
necessary, temporarily substitute mypy for the typing gate without changing the gate contract.

---

## 8. Testing framework: pytest

**Decision**: **pytest** configured under `[tool.pytest.ini_options]`, with a smoke test that keeps
the suite green from day one and a gate self-test that asserts `tests/fixtures/bad_example.py`
trips the gates.

**Rationale**: pytest is the ecosystem standard and is mandated by the constitution's Testing
Standards. Configuring it in `pyproject.toml` satisfies the single-config rule. The self-test makes
SC-003 executable: it proves the gates actually catch a style violation, a likely bug, a hard-coded
secret, and a type error.

**Alternatives considered**:
- *unittest*: stdlib, but less ergonomic and not idiomatic for a modern stack.

---

## 9. CI enforcement

**Decision**: **GitHub Actions** workflow (`.github/workflows/quality.yml`) that installs uv, syncs
the locked environment, and runs the same `poe check` on every pull request to `main`; a required
status check blocks merge on failure (FR-005/SC-002).

**Rationale**: GitHub Actions is the default for GitHub-hosted repos; running the identical
`poe check` guarantees local/CI verdict parity (FR-006/SC-005). Setting the job as a required check
operationalizes the constitution's "all gates green to merge".

**Alternatives considered**:
- *pre-commit only*: local, bypassable; does not protect the branch. May be added later as a
  convenience but is not the enforcement mechanism.
- *Other CI providers*: fine in principle; GitHub Actions assumed as the hosting default.

---

## 10. Suppression policy (auditable false positives)

**Decision**: Allow tool-native inline suppressions that REQUIRE a reason: `# noqa: <rule>` (ruff),
`# pylint: disable=<check>` with an adjacent justification comment, `# nosec <test-id>` (bandit),
and ty's inline ignore syntax. Blanket, file-wide, or unexplained disables are disallowed by review.

**Rationale**: Satisfies FR-009/SC-007 — a single finding can be silenced with a recorded reason
without weakening the gate elsewhere. Enforced socially via code review (constitution: exceptions
documented per-change), and ruff's `RUF100` flags unused/blanket `noqa` to keep suppressions honest.

**Alternatives considered**:
- *Global disables in config*: rejected — weakens coverage repo-wide and hides intent.

---

## 11. Line length

**Decision**: **120 characters**, set once as ruff `line-length = 120` and mirrored by pylint
`max-line-length = 120`. ruff `format` wraps to 120 and ruff `E501` flags overflow; pylint uses the
same limit so no gate disagrees on wrap width.

**Rationale**: 120 is the modern, widely adopted width that suits current wide displays and reduces
awkward wrapping versus the older 79/88 defaults, while still keeping side-by-side diffs readable.
Centralizing the number in `pyproject.toml` and reusing it across gates preserves the single-source
-of-truth and local/CI-parity guarantees (FR-006/FR-010).

**Alternatives considered**:
- *88 (ruff/black default)*: fine but narrower than requested; would force more wrapping.
- *79 (PEP 8 classic)*: too tight for a modern codebase.
- *No limit*: rejected — inconsistent formatting and unreviewable long lines.

---

## Resolved unknowns summary

| Unknown | Resolution |
|---------|------------|
| Package/env manager | uv + committed `uv.lock` |
| Build backend | hatchling, PEP 621, `requires-python = ">=3.12"` |
| Single command mechanism | poethepoet `[tool.poe.tasks]` → `poe check` |
| Strong rule sets | Enumerated ruff `select`, high-signal pylint, bandit, ty |
| Type checker choice | ty primary; mypy documented fallback |
| CI provider & enforcement | GitHub Actions required check on PRs to `main` |
| Suppression mechanism | Reasoned inline suppressions only; RUF100 guards |
| Line length | 120 chars — ruff `line-length` + pylint `max-line-length`, single source |

No open NEEDS CLARIFICATION items remain.
