---

description: "Task list for CLI Progress Logging & Verbose Mode implementation"
---

# Tasks: CLI Progress Logging & Verbose Mode

**Input**: Design documents from `/specs/004-cli-logging/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/logging-contract.md, quickstart.md

**Tests**: Test tasks ARE included — the spec defines validation scenarios and the constitution's
Testing Standards are non-negotiable.

**Organization**: Grouped by user story so each is an independently testable increment.

> **Extends existing code**: This feature modifies `cli.py`, `pipeline.py`, `config/loader.py`,
> `content/resolver.py`, `render/html_renderer.py`, and `pdf/weasyprint_pdf.py` from
> `002-pdf-generation`/`003-edition-revisions`. No new third-party dependencies — stdlib `logging`
> only, per plan.md.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1, US2, US3

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: The logging configuration entry point and test scaffolding.

- [X] T001 Create `src/wh40k_cheatsheet/logging_setup.py` with `configure_logging(verbose: bool) -> None`: sets the `wh40k_cheatsheet` package logger's level to `DEBUG` if `verbose` else `INFO`, and attaches one `logging.StreamHandler(sys.stderr)` with formatter `"%(levelname)s %(name)s: %(message)s"` (research.md §6; contracts/logging-contract.md)
- [X] T002 [P] Create `tests/unit/__init__.py` and `tests/integration/__init__.py` test package scaffolding

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Wire the `--verbose` flag and per-module loggers that every story's log calls attach to.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 Add a top-level `-v`/`--verbose` boolean flag (default `False`) to the argument parser in `src/wh40k_cheatsheet/cli.py` and call `configure_logging(args.verbose)` in `main()` before dispatching to the subcommand handler (depends on T001; research.md §4)
- [X] T004 [P] Add a module-level `logger = logging.getLogger(__name__)` to `src/wh40k_cheatsheet/pipeline.py`, `src/wh40k_cheatsheet/config/loader.py`, `src/wh40k_cheatsheet/content/resolver.py`, `src/wh40k_cheatsheet/render/html_renderer.py`, and `src/wh40k_cheatsheet/pdf/weasyprint_pdf.py` (declarations only; no calls yet — data-model.md logger hierarchy)

**Checkpoint**: Flag exists and configures the logger; every module has a logger ready to use. No log lines emitted yet.

---

## Phase 3: User Story 1 - See what the generator is doing while it runs (Priority: P1) 🎯 MVP

**Goal**: A default (non-verbose) `generate` run prints an ordered `INFO` line per major stage to
stderr, while stdout's existing result output is unchanged.

**Independent Test**: `generate --edition 11e --language en` shows `INFO` lines for config-loaded,
revision-resolved, content-resolved, template-rendered, and PDF-converted, in that order, followed by
the existing stdout success line.

### Tests for User Story 1 ⚠️

- [X] T005 [US1] Integration test: default `generate` run emits one `INFO` stage message (config loaded, revision resolved, content resolved, template rendered, PDF converted) in execution order on stderr, and stdout's result line is byte-identical to the pre-feature output, in `tests/integration/test_generate_logging.py` (FR-001/FR-002/FR-009; SC-001)
- [X] T006 [P] [US1] Integration test: `list` output is unchanged from before this feature (no new step-by-step logging required) in `tests/integration/test_list_logging.py` (US1-3)

### Implementation for User Story 1

- [X] T007 [US1] Log `INFO "configuration loaded"` after a successful load in `src/wh40k_cheatsheet/config/loader.py` (FR-001)
- [X] T008 [US1] Log `INFO "[edition/revision/language] resolving revision"`, `"...resolving content"` at the corresponding steps in `src/wh40k_cheatsheet/pipeline.py`, prefixing every message with the `(edition_id, revision_id, language)` triple (FR-001/FR-003; research.md §5)
- [X] T009 [US1] Log `INFO "[edition/revision/language] template rendered"` after a successful render in `src/wh40k_cheatsheet/render/html_renderer.py` (FR-001/FR-003)
- [X] T010 [US1] Log `INFO "[edition/revision/language] PDF converted"` after a successful conversion in `src/wh40k_cheatsheet/pdf/weasyprint_pdf.py` (FR-001/FR-003)

**Checkpoint**: MVP — a default `generate` run is fully visible stage-by-stage; `list` unaffected.

---

## Phase 4: User Story 2 - Get detailed diagnostic output on demand (Priority: P2)

**Goal**: `--verbose` adds `DEBUG` diagnostic detail (resolved paths, chosen template/revision) on
top of the default `INFO` lines, without changing any generated file.

**Independent Test**: Run the same `generate` command once plain and once with `--verbose`; the
verbose run prints additional `DEBUG` lines and produces byte-identical `.html`/`.pdf` output.

### Tests for User Story 2 ⚠️

- [X] T011 [P] [US2] Integration test: `--verbose` adds `DEBUG` lines (resolved paths, chosen template/revision) beyond the default `INFO` lines, and omitting the flag reproduces exactly the default-level output from US1's test, in `tests/integration/test_generate_logging.py` (FR-004/FR-005; SC-002)
- [X] T012 [P] [US2] Integration test: generating the same (edition, revision, language) once without and once with `--verbose` produces byte-identical `.html` and `.pdf` files, in `tests/integration/test_verbose_output_parity.py` (FR-006; SC-003)

### Implementation for User Story 2

- [X] T013 [US2] Log `DEBUG` with the resolved `project.yaml` path in `src/wh40k_cheatsheet/config/loader.py` (FR-005)
- [X] T014 [US2] Log `DEBUG` with the resolved content file path in `src/wh40k_cheatsheet/content/resolver.py` (FR-005)
- [X] T015 [US2] Log `DEBUG` with the resolved template name in `src/wh40k_cheatsheet/render/html_renderer.py` (FR-005)
- [X] T016 [US2] Log `DEBUG` with the output PDF path in `src/wh40k_cheatsheet/pdf/weasyprint_pdf.py` (FR-005)

**Checkpoint**: US1 and US2 both work — default stays concise, `--verbose` adds detail, output files unaffected.

---

## Phase 5: User Story 3 - Errors are always visible regardless of verbosity (Priority: P3)

**Goal**: Run-terminating failures are logged at `CRITICAL` and remain clearly visible and
distinguishable at both default and verbose levels.

**Independent Test**: Trigger a known failure (unknown edition) once at default and once with
`--verbose`; the `CRITICAL` line is present, visible, and not buried in either case.

### Tests for User Story 3 ⚠️

- [X] T017 [P] [US3] Integration test: an unknown-edition failure logs a `CRITICAL` line and exits non-zero at both default and `--verbose` levels, in `tests/integration/test_generate_logging.py` (FR-007; SC-004)
- [X] T018 [P] [US3] Integration test: with `--verbose` producing many `DEBUG` lines, the `CRITICAL` failure line remains distinguishable by its level-name prefix, in `tests/integration/test_critical_visibility.py` (FR-008)

### Implementation for User Story 3

- [X] T019 [US3] Replace the bare `print(f"Error: {exc}", file=sys.stderr)` in `src/wh40k_cheatsheet/cli.py` with `logger.critical(f"Error: {exc}")` using a module logger, preserving the existing exit-code-1 behavior (FR-007/FR-008; contracts/logging-contract.md)

**Checkpoint**: All three stories independently functional — visible by default, detailed on demand, failures never hidden.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation and documentation.

- [X] T020 Run every scenario in `quickstart.md` end-to-end (default stage visibility, verbose detail + output parity, multi-language attribution, error visibility at both levels, `list` unaffected) and confirm expected outcomes
- [X] T021 [P] Update `README.md` with `-v`/`--verbose` usage, the level table (DEBUG/INFO/WARNING/CRITICAL and why `ERROR` is unused), and the stderr/stdout split

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories (flag + loggers must exist before any log call is added).
- **US1 (Phase 3)**: Depends on Foundational. The MVP.
- **US2 (Phase 4)**: Depends on US1's `INFO` calls existing (adds `DEBUG` alongside them in the same modules).
- **US3 (Phase 5)**: Depends on Foundational (the `cli.py` logger); independent of US1/US2's specific log calls.
- **Polish (Phase 6)**: After the desired stories.

### User Story Dependencies

- **US1 (P1)**: Independent once Foundational is done.
- **US2 (P2)**: Extends the same modules US1 touches — sequenced after US1 to avoid rework, though logically additive.
- **US3 (P3)**: Touches only `cli.py`'s failure path — independent of US1/US2's per-stage calls.

### Within Each User Story

- Tests before implementation (T005/T006 before T007–T010; T011/T012 before T013–T016; T017/T018 before T019).
- Each module's `INFO` call (US1) and `DEBUG` call (US2) are separate edits to the same file → sequenced, not parallel, within a module.

### Parallel Opportunities

- **Setup**: T002 is independent of T001.
- **Foundational**: T004 touches five different files → could be split further, but is grouped as one task since it's a single trivial declaration per file.
- **US1**: T006 (list test) is parallel to T005 (generate test); T007–T010 touch four different modules → parallelizable once T005/T006 exist, though each depends on Foundational's T004 for that specific module.
- **US2**: T011/T012 (tests) parallel; T013–T016 touch four different modules → parallelizable.
- **US3**: T017/T018 (tests) parallel.
- **Polish**: T021 parallel to T020.

---

## Parallel Example: User Story 1 implementation

```bash
# Different files, each adding one INFO call — independent once T004's loggers exist:
Task: "Log INFO 'configuration loaded' in src/wh40k_cheatsheet/config/loader.py"
Task: "Log INFO stage messages in src/wh40k_cheatsheet/pipeline.py"
Task: "Log INFO 'template rendered' in src/wh40k_cheatsheet/render/html_renderer.py"
Task: "Log INFO 'PDF converted' in src/wh40k_cheatsheet/pdf/weasyprint_pdf.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T002).
2. Complete Phase 2: Foundational (T003–T004) — CRITICAL, blocks all stories.
3. Complete Phase 3: User Story 1 (T005–T010).
4. **STOP and VALIDATE**: default `generate` run shows ordered `INFO` stage lines; stdout unchanged.
5. Demonstrable MVP — visibility into what the generator is doing, by default.

### Incremental Delivery

1. Setup + Foundational → flag and loggers ready.
2. US1 → default stage visibility (MVP!) → validate → demo.
3. US2 → `--verbose` diagnostic detail with output-parity guarantee → validate → demo.
4. US3 → failures always visible/distinguishable → validate → demo.
5. Polish → quickstart validation + docs.

---

## Notes

- [P] = different files, no dependencies. Tasks sharing a file (e.g., `cli.py`) run serially.
- [Story] label maps each task to its user story for traceability.
- Tests (T005/T006, T011/T012, T017/T018) must fail before their implementation lands.
- No new dependencies — stdlib `logging` only.
- Commit after each task or logical group; stop at any checkpoint to validate a story independently.
