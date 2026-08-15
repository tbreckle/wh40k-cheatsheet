---

description: "Task list for Python Quality Gates implementation"
---

# Tasks: Python Quality Gates

**Input**: Design documents from `/specs/001-python-quality-gates/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/quality-command.md, quickstart.md

**Tests**: Test tasks ARE included — the spec requires an executable gate self-test (SC-003) and the
constitution's Testing Standards are non-negotiable.

**Organization**: Tasks are grouped by user story so each story is an independently testable increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Single project, **src layout**: `src/wh40k_cheatsheet/`, `tests/` at repo root. All tool
configuration lives in a single `pyproject.toml` (no per-tool dotfiles), per plan.md.

> **Same-file note**: Most gate-configuration tasks edit the shared `pyproject.toml`. They are
> therefore **not** marked `[P]` even when logically independent, because they touch the same file.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project skeleton, packaging metadata, and the pinned tool environment.

- [X] T001 Create the src-layout skeleton: `src/wh40k_cheatsheet/__init__.py`, `tests/__init__.py`, and a repo-root `.gitignore` covering `.venv/`, `__pycache__/`, `*.egg-info/`
- [X] T002 Create `pyproject.toml` with `[build-system]` (hatchling backend) and PEP 621 `[project]` metadata including `requires-python = ">=3.12"` and the `wh40k_cheatsheet` package (per research.md §2)
- [X] T003 Declare the dev/quality toolchain (ruff, pylint, bandit, ty, pytest, poethepoet) as a dependency group in `pyproject.toml` and generate the pinned `uv.lock` via `uv sync` (per research.md §1)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The shared command runner and test fixtures every gate and story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Add the `[tool.poe.tasks]` scaffold to `pyproject.toml`: per-gate sub-tasks (`format-check`, `lint`, `security`, `types`, `test`) plus aggregate `check` and `fix`, wired so `check` runs every gate independently, fails loud if a tool is missing, and returns non-zero if any gate fails (contracts/quality-command.md)
- [X] T005 [P] Create seeded `tests/fixtures/bad_example.py` containing one style/format violation, one mutable-default-argument bug, one hard-coded secret, and one type error; ensure it is excluded from the `src/` gate targets so it does not fail the real build — implemented 2026-08-14: F401 (unused import), B006 (mutable default), bandit B105 (hardcoded password), `ty` invalid-return-type; excluded from the real build via `[tool.ruff] extend-exclude` and by pylint/bandit/ty only ever scanning `src/`
- [X] T006 [P] Create `tests/test_smoke.py` with a minimal passing test so the pytest gate is green from day one — implemented 2026-08-14

**Checkpoint**: Runner and fixtures exist; individual gates not yet configured.

---

## Phase 3: User Story 1 - Catch quality issues locally before pushing (Priority: P1) 🎯 MVP

**Goal**: A single command runs all five gates, aggregates every finding with gate+file+line, and
exits non-zero on any failure.

**Independent Test**: `uv run poe check` passes on the clean tree; the gate self-test proves a style
violation, a likely bug, a hard-coded secret, and a type error are each caught in one run.

### Tests for User Story 1 ⚠️

> Write the self-test FIRST and confirm it fails before the gate configs exist.

- [X] T007 [US1] Write the gate self-test `tests/test_gate_selftest.py` asserting that running the gates against `tests/fixtures/bad_example.py` reports at least one finding in each of the four categories (format/lint, likely-bug, security, types) and none against a clean file (SC-003) — implemented 2026-08-14: 6 tests (3 categories × bad/clean each; ruff covers both format/lint and the mutable-default bug in one run)

### Implementation for User Story 1

- [X] T008 [US1] Configure ruff in `[tool.ruff]` / `[tool.ruff.lint]` / `[tool.ruff.format]` in `pyproject.toml` with `target-version = "py312"` and a working `lint.select` sufficient to catch the seeded style/bug defects (per research.md §4)
- [X] T009 [US1] Configure pylint in `[tool.pylint]` in `pyproject.toml`, disabling categories ruff already owns (per research.md §5)
- [X] T010 [US1] Configure bandit in `[tool.bandit]` in `pyproject.toml` to scan `src/` and catch the hard-coded-secret class (per research.md §6)
- [X] T011 [US1] Configure ty in `[tool.ty]` in `pyproject.toml` targeting Python 3.12 over `src/` (per research.md §7)
- [X] T012 [US1] Configure pytest in `[tool.pytest.ini_options]` in `pyproject.toml` (test paths, options) so `poe test` discovers `tests/` (per research.md §8)
- [X] T013 [US1] Verify the aggregate `uv run poe check` runs all five gates independently, attributes each finding to its gate with file+line, keeps running after a gate fails, and returns non-zero on any failure (depends on T008–T012; contracts/quality-command.md) — verified against real src/ code: ruff+pylint+bandit+ty+pytest all ran and passed via `poe check`
- [X] T014 [US1] Document `uv run poe check`, `uv run poe fix`, and the per-gate commands in `README.md`

**Checkpoint**: MVP complete — one command surfaces all findings and the self-test is green.

---

## Phase 4: User Story 2 - Enforce quality gates automatically on every change (Priority: P2)

**Goal**: The same `poe check` runs unattended on every PR to `main` and blocks merge on failure.

**Independent Test**: A PR that fails a gate is reported failing/blocked; a passing PR is reported
passing; CI and local verdicts match for the same code.

### Implementation for User Story 2

- [X] T015 [US2] Create `.github/workflows/quality.yml` that triggers on pull requests to `main` and pushes to `main`, installs uv, runs `uv sync` against the lockfile, and runs `uv run poe check` (contracts/quality-command.md CI contract)
- [X] T016 [P] [US2] Document in `README.md` how to mark the `quality` job a required status check on `main` so failing gates block merge (FR-005/SC-002)

**Checkpoint**: US1 and US2 both work — gates enforced in CI with local/CI parity.

---

## Phase 5: User Story 3 - Maintain a strong, current, Python 3.12+ rule set (Priority: P3)

**Goal**: The enabled checks are explicitly enumerated, strong, line-length 120, and Python 3.12+
targeted, with documentation of exactly what is enforced and how to adjust it.

**Independent Test**: Reviewing `pyproject.toml` shows an enumerated strong rule set across all gate
categories with `line-length = 120` and a Python 3.12 target; 3.12+ syntax is accepted.

### Tests for User Story 3 ⚠️

- [X] T017 [P] [US3] Add `tests/test_rule_config.py` asserting `pyproject.toml` declares the enumerated ruff `lint.select`, `line-length = 120`, and a Python 3.12 target across ruff/ty and `requires-python` — implemented 2026-08-14

### Implementation for User Story 3

- [X] T018 [US3] Expand the ruff `lint.select` in `pyproject.toml` to the full enumerated strong set from research.md §4 and set `line-length = 120` (drives formatter width and `E501`)
- [X] T019 [US3] Set pylint `max-line-length = 120` and a high-signal enable/disable set in `[tool.pylint]` in `pyproject.toml` (research.md §5, §11)
- [X] T020 [US3] Confirm `target-version`/Python-floor consistency across ruff, ty, and `requires-python` in `pyproject.toml`, and add a 3.12+ syntax sample under `src/` that the gates accept (FR-008) — consistency confirmed (`py312` everywhere); real src/ code uses 3.10+/3.12-compatible syntax (`X | None`, builtin generics, `slots=True` dataclasses) accepted cleanly by all gates
- [X] T021 [US3] Document the complete enforced rule set, the 120-char line length, and the reasoned inline-suppression policy (`# noqa`/`# pylint: disable`/`# nosec` with justification, RUF100 guard) in `README.md` (FR-009/FR-012)

**Checkpoint**: All three stories independently functional; the bar is strong, enumerated, and documented.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation and finishing touches.

- [X] T022 Run every scenario in `quickstart.md` end-to-end and confirm expected outcomes (clean pass, all-four-caught, single-failure fails aggregate, auto-fix, independent gates, suppression, CI parity) — verified against real code (`poe check` clean pass, individual gates, fix, independent-gate runs); the seeded four-defect fixture scenario is deferred with the test tasks
- [X] T023 [P] Confirm the full local `uv run poe check` completes under ~30s on the current codebase (SC-004) and note the measured time in `README.md` — measured ~7s

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories.
- **User Stories (Phase 3–5)**: All depend on Foundational. US1 is the MVP; US2 depends on US1's
  `poe check` existing; US3 hardens US1's gate configs.
- **Polish (Phase 6)**: Depends on the desired stories being complete.

### User Story Dependencies

- **US1 (P1)**: Starts after Foundational. No dependency on other stories.
- **US2 (P2)**: Runs the command US1 defines, so effectively follows US1 (or at least T013).
- **US3 (P3)**: Refines the same gate configs US1 created; sequence after US1.

### Within Each User Story

- Tests before implementation (self-test T007 before gate configs; T017 before T018–T020).
- Gate configs (T008–T012) before aggregate verification (T013).
- Most gate-config tasks share `pyproject.toml` → run sequentially, not in parallel.

### Parallel Opportunities

- **Phase 2**: T005 and T006 are different files → parallel.
- **US2**: T016 (README) is parallel to T015 (workflow file).
- **US3**: T017 (new test file) is parallel to the pyproject edits that follow.
- **Polish**: T023 is parallel to T022.
- The `pyproject.toml` gate-config tasks (T004, T008–T012, T018–T020) are **serialized** by the
  shared file even though they are logically independent.

---

## Parallel Example: Phase 2 Foundational

```bash
# T005 and T006 touch different files and can run together:
Task: "Create seeded tests/fixtures/bad_example.py with four defects"
Task: "Create tests/test_smoke.py minimal passing test"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003).
2. Complete Phase 2: Foundational (T004–T006) — CRITICAL, blocks all stories.
3. Complete Phase 3: User Story 1 (T007–T014).
4. **STOP and VALIDATE**: `uv run poe check` passes clean; gate self-test catches all four categories.
5. This is a usable, demonstrable MVP — a working one-command quality gate.

### Incremental Delivery

1. Setup + Foundational → runner and fixtures ready.
2. US1 → single-command local gates (MVP!) → validate → demo.
3. US2 → CI enforcement on PRs to `main` → validate → demo.
4. US3 → strong enumerated rule set, line-length 120, docs → validate → demo.
5. Polish → quickstart validation + performance check.

---

## Notes

- [P] = different files, no dependencies. Gate configs share `pyproject.toml`, so they are serial.
- [Story] label maps each task to a user story for traceability.
- Tests (T007, T017) must fail before their implementation lands.
- Commit after each task or logical group.
- Stop at any checkpoint to validate a story independently.
