# Implementation Plan: Python Quality Gates

**Branch**: `001-python-quality-gates` | **Date**: 2026-08-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-python-quality-gates/spec.md`

## Summary

Establish a single-command, CI-enforced quality gate suite for the WH40K Cheatsheet project using
an ultra-modern Python 3.12+ stack. All tool configuration lives in `pyproject.toml`: **ruff**
(format + fast lint), **pylint** (deep correctness lint), **bandit** (security), **ty** (type
checking), and **pytest** (tests). A task runner defined in `pyproject.toml` provides one command
that runs every gate and aggregates findings; the same command runs unattended in CI and blocks
merges on failure. Packaging and build metadata are defined in `pyproject.toml` via a modern build
backend, with `uv` as the environment/dependency manager.

## Technical Context

**Language/Version**: Python 3.12+ (minimum supported is 3.12; `requires-python = ">=3.12"`)

**Primary Dependencies**: Dev/quality toolchain — ruff, pylint, bandit, ty, pytest, plus a
`pyproject.toml`-native task runner (poethepoet) for the aggregate command. `uv` as the package and
environment manager. No runtime application dependencies are introduced by this feature.

**Storage**: N/A — all configuration is version-controlled in `pyproject.toml`.

**Testing**: pytest (with pytest configuration in `[tool.pytest.ini_options]`); a seeded
"bad example" fixture proves each gate catches its category.

**Target Platform**: Local developer machines (Linux/macOS/Windows) and the CI runner
(GitHub Actions, Linux).

**Project Type**: Single project — tooling/infrastructure layer that all future application code
(the cheatsheet itself) will sit under.

**Performance Goals**: Full local gate run completes in under 30 seconds on a typical developer
machine on the current (small) codebase (SC-004).

**Constraints**: All tool configuration MUST reside in `pyproject.toml` (no scattered `.ruff.toml`,
`.pylintrc`, `.bandit`, etc.). Local and CI runs MUST share that single configuration and produce
identical verdicts (FR-006). Each gate runs independently (FR-004). Python < 3.12 is out of scope.
Line length is standardized at **120 characters** across formatter and linters.

**Scale/Scope**: Greenfield repository; this feature sets up the quality foundation before any
application code exists. Expected to scale to the full cheatsheet codebase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment |
|-----------|------------|
| I. Code Quality | **Directly satisfied.** This feature *is* the tooling-enforced lint/format/type bar the principle mandates. ruff+pylint enforce style and correctness; ty enforces types; all gate merges. |
| II. Testing Standards (NON-NEGOTIABLE) | **Satisfied & advanced.** Introduces pytest as the sanctioned suite and a seeded regression fixture proving each gate. Gate config itself is validated by a test that the "bad example" fails and a clean file passes. |
| III. User Experience Consistency | **N/A to end-user UX** (no user-facing surface). The "user" here is the contributor; the single-command, consistent local/CI verdict serves the same predictability goal. |
| IV. Performance Requirements | **Satisfied (developer-facing).** SC-004 sets a <30s local-run budget so the gate stays fast enough to run before every push, honoring the principle's "fast feedback" intent. |
| Additional Constraints & Standards | **Satisfied.** Config is structured, version-controlled, human-reviewable (single `pyproject.toml`); dependencies are pinned via `uv` lockfile; no secrets introduced. |
| Development Workflow & Quality Gates | **Directly satisfied.** PR-only enforcement, all-gates-green-to-merge, auditable inline suppressions with justification. |

**Verdict**: PASS. No violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/001-python-quality-gates/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── quality-command.md
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
pyproject.toml           # PEP 621 metadata, build backend, and ALL tool config
                         #   [build-system], [project], [tool.ruff], [tool.pylint],
                         #   [tool.bandit], [tool.ty], [tool.pytest.ini_options],
                         #   [tool.poe.tasks]
uv.lock                  # Pinned, reproducible dependency lock (uv)
README.md                # How to run the gates locally (references quickstart)

src/
└── wh40k_cheatsheet/    # Application package (src layout; empty __init__ for now)
    └── __init__.py

tests/
├── __init__.py
├── test_smoke.py        # Minimal passing test so pytest gate is green from day one
└── fixtures/
    └── bad_example.py   # Seeded file that MUST trip every gate (used by gate self-test)

.github/
└── workflows/
    └── quality.yml      # CI: runs the same aggregate command on PRs to main
```

**Structure Decision**: Single-project **src layout**. The `src/wh40k_cheatsheet/` package is the
future home of the cheatsheet application; this feature only seeds it so the gates have real targets
and packaging is valid. Every tool's configuration is centralized in `pyproject.toml` per the user
directive; no per-tool dotfiles are created. The aggregate quality command is a poethepoet task
(`[tool.poe.tasks]`) so both humans and CI invoke the identical entrypoint.

## Complexity Tracking

> No constitution violations. Section intentionally left empty.
