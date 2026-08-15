---

description: "Task list for Google-Style Docstrings Everywhere implementation"
---

# Tasks: Google-Style Docstrings Everywhere

**Input**: Design documents from `/specs/008-google-style-docstrings/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/docstring-style.md, quickstart.md

**Tests**: Test tasks ARE included — the spec's User Story 2 is specifically about automated
enforcement, and the constitution's Testing Standards are non-negotiable.

**Organization**: Grouped by user story so each is an independently testable increment.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1, US2, US3

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Configure the quality-gate tooling so every docstring added afterward is verified as
it's written, rather than in one blind pass at the end.

- [X] T001 Update `pyproject.toml` per the gate configuration contract (`contracts/docstring-style.md`): add `"D"` to `[tool.ruff.lint] select`; add `[tool.ruff.lint.pydocstyle] convention = "google"`; append `"D"` to the `"tests/**"` entry in `[tool.ruff.lint.per-file-ignores]`; remove `missing-module-docstring`/`missing-class-docstring`/`missing-function-docstring` from `[tool.pylint."messages control"] disable`; add `load-plugins = ["pylint.extensions.docparams"]` to `[tool.pylint.main]`; add `[tool.pylint.basic] no-docstring-rgx = "^$"`; add `[tool.pylint.parameter_documentation]` with `accept-no-param-doc = false`, `accept-no-return-doc = false`, `accept-no-raise-doc = false`, `accept-no-yields-doc = false`, `default-docstring-type = "google"` (research.md §1/§2; data-model.md Gate Configuration entity)

**Checkpoint**: `poe lint` now reports every currently-undocumented symbol in `src/` (55 ruff `D` findings on public symbols, 65 pylint findings on public+private — research.md's baseline measurement). This is expected and is exactly what Phase 3 fixes.

---

## Phase 2: Foundational (Blocking Prerequisites)

No additional foundational work beyond Phase 1's gate configuration — there is no shared
infrastructure, model, or service layer for a documentation feature. Every task in Phase 3 (US1)
touches a distinct, independent file and has no cross-task dependency.

---

## Phase 3: User Story 1 - Understand any module, class, or function without reading its implementation (Priority: P1) 🎯 MVP

**Goal**: Every module, class, function, and method in `src/wh40k_cheatsheet` — public and private —
has a Google-style docstring, so `pydoc`/`help()`/an IDE tooltip is enough to understand it.

**Independent Test**: Run `python -m pydoc wh40k_cheatsheet.<any module>` (or `help()`) on any module
and confirm every class/function shows a non-empty, Google-style docstring including a summary,
`Args:`, and `Returns:` (where applicable) — per `contracts/docstring-style.md`'s authoring contract.

### Implementation for User Story 1

- [X] T002 [P] [US1] Add a module docstring to `src/wh40k_cheatsheet/__init__.py` (currently a 0-byte file — summary of the package as a whole; FR-001 edge case, research.md §4)
- [X] T003 [P] [US1] Add module + function docstrings to `src/wh40k_cheatsheet/cli.py`: module docstring, plus `_default_paths`, `_cmd_generate`, `_cmd_list`, `_add_verbose_flag`, `build_parser`, `main` (contracts/docstring-style.md function template; `KNOWN_ERRORS` is a module-level constant, not a def, so no docstring applies to it)
- [X] T004 [P] [US1] Add module + function docstrings to `src/wh40k_cheatsheet/logging_setup.py`: module docstring, plus `configure_logging`
- [X] T005 [P] [US1] Add module + class + function docstrings to `src/wh40k_cheatsheet/pipeline.py`: module docstring; `PipelineError`; `Paths`, `GeneratedDocument`, `EditionInventory` dataclasses each with an `Attributes:` section listing their fields; `_resolve_edition`, `_resolve_revision`, `_resolve_languages`, `_generate_one`, `generate`, `list_inventory`
- [X] T006 [P] [US1] Add a module docstring to `src/wh40k_cheatsheet/config/__init__.py` (re-export-only module; FR-001 edge case)
- [X] T007 [P] [US1] Add module + function docstrings to `src/wh40k_cheatsheet/config/loader.py`: module docstring; `ConfigError`; `load_project_config`
- [X] T008 [P] [US1] Add module + class + method docstrings to `src/wh40k_cheatsheet/config/models.py`: module docstring; `LanguageEntry`, `Edition` (with `Attributes:`), `ProjectConfig` (with `Attributes:`); `Edition._languages_non_empty`, `Edition.resolve_template`, `ProjectConfig._editions_non_empty`, `ProjectConfig.list_editions`, `ProjectConfig.list_languages` — includes the two private pydantic validators, in scope per FR-006
- [X] T009 [P] [US1] Add a module docstring to `src/wh40k_cheatsheet/content/__init__.py` (re-export-only module; FR-001 edge case)
- [X] T010 [P] [US1] Add module + function docstrings to `src/wh40k_cheatsheet/content/resolver.py`: module docstring; `ContentError`; `resolve_content`
- [X] T011 [P] [US1] Add a module docstring to `src/wh40k_cheatsheet/pdf/__init__.py` (re-export-only module; FR-001 edge case)
- [X] T012 [P] [US1] Add module + function docstrings to `src/wh40k_cheatsheet/pdf/weasyprint_pdf.py`: module docstring; `PdfError`; `render_pdf`
- [X] T013 [P] [US1] Add a module docstring to `src/wh40k_cheatsheet/render/__init__.py` (re-export-only module; FR-001 edge case)
- [X] T014 [P] [US1] Add module + class + function docstrings to `src/wh40k_cheatsheet/render/html_renderer.py`: module docstring; `RenderError`; `Segment` dataclass (with `Attributes:`); `group_by_breaks`, `_environment`, `render_html`
- [X] T015 [P] [US1] Add a module docstring to `src/wh40k_cheatsheet/revision/__init__.py` (re-export-only module; FR-001 edge case)
- [X] T016 [P] [US1] Add module + class + function docstrings to `src/wh40k_cheatsheet/revision/discovery.py`: module docstring; `NoRevisionsError`, `RevisionNotFoundError`, `MalformedRevisionDirectoryError`; `Revision`, `RevisionSet` dataclasses (with `Attributes:`) plus `RevisionSet.latest`, `RevisionSet.get`, `RevisionSet.ids`; `discover_revisions`
- [X] T017 [P] [US1] Add module + class + method docstrings to `src/wh40k_cheatsheet/revision/identifier.py`: module docstring; `InvalidRevisionIdError`; `RevisionId` dataclass (with `Attributes:`) plus `RevisionId.parse`, `RevisionId.__str__`, `RevisionId.__lt__` — the two dunder methods are not exempt (research.md §3)

**Checkpoint**: MVP — every symbol in `src/` is documented; `poe lint` should now report zero `D`/`missing-*-docstring`/`docparams` findings (verified formally in Phase 5).

---

## Phase 4: User Story 2 - Enforcement prevents undocumented code from being merged (Priority: P2)

**Goal**: The gate configured in Phase 1 is proven to actually catch a missing or inaccurate
docstring, not merely assumed to work because the config keys are set.

**Independent Test**: Add an undocumented function (or one with a mismatched `Args:`/`Returns:`)
on a scratch fixture and confirm the gate fails with the exact expected rule/message; add a fully
compliant fixture and confirm it passes clean.

### Tests for User Story 2 ⚠️

- [X] T018 [P] [US2] Unit test asserting the `pyproject.toml` settings from T001 are exactly what research.md/contracts specify (ruff `D` in `select`, `pydocstyle.convention == "google"`, `"D"` in the `tests/**` per-file-ignore, pylint's `no-docstring-rgx == "^$"`, `docparams` in `load-plugins`, all four `accept-no-*-doc` are `false`) in `tests/unit/test_docstring_gate_config.py` (FR-005; data-model.md Gate Configuration entity)
- [X] T019 [P] [US2] Create a seeded fixture with one undocumented function, one class with an undocumented method, and one function whose Google-style docstring omits a real parameter and claims a nonexistent one, in `tests/unit/fixtures/bad_docstring_example.py` (excluded from `poe lint`'s real gate targets the same way `tests/**` already is — used only by direct subprocess invocation in T021)
- [X] T020 [P] [US2] Create a fully Google-style-compliant fixture mirroring the same shapes (documented function, documented class/method, function with fully accurate `Args:`/`Returns:`) in `tests/unit/fixtures/good_docstring_example.py`
- [X] T021 [US2] Integration test: run `pylint` as a subprocess directly against `tests/unit/fixtures/bad_docstring_example.py`, asserting a non-zero exit and `missing-function-docstring`/`missing-param-doc`/`differing-param-doc` appear in the output; repeat against `good_docstring_example.py` asserting none of the docstring-related codes appear, in `tests/integration/test_docstring_gate_selftest.py` (depends on T019, T020; contracts/docstring-style.md behavioral contract items 2–3, 5) — pylint only, not ruff: ruff's `"tests/**"` per-file-ignore (T001) exempts any file under `tests/` from `D` codes regardless of how ruff is invoked, so a `tests/`-located fixture can't demonstrate ruff's D-rule behavior; ruff's public-scope enforcement is already proven directly, since the real `src/` retrofit (T002–T017) went from 55 `D` findings to 0

### Implementation for User Story 2

- No story-specific implementation — Phase 1's gate configuration (T001) already delivers the
  enforcement mechanism; T018–T021 verify it against the P2 acceptance criteria.

**Checkpoint**: The enforcement mechanism is proven, not assumed — a missing or inaccurate docstring
reliably fails the gate, and compliant code reliably passes.

---

## Phase 5: User Story 3 - Existing code is retrofitted, not just new code (Priority: P3)

**Goal**: The current `src/` tree — not just future changes — is fully compliant immediately upon
shipping this feature.

**Independent Test**: Run the gate from Phase 1/4 against the repository as it stands after Phase 3
and confirm zero missing/malformed docstring findings.

### Implementation for User Story 3

- No story-specific implementation — Phase 3's retrofit (T002–T017) already covers every existing
  file; this phase only formally verifies zero violations remain.

- [X] T022 [US3] Run `uv run poe lint` against the full repository and confirm zero `D`-rule and zero `missing-*-docstring`/`docparams` findings anywhere in `src/wh40k_cheatsheet` (FR-007; SC-001, SC-004) — depends on T002–T017 (Phase 3) and T001 (Phase 1) being complete

**Checkpoint**: All three stories independently functional — docstrings exist and are readable
(US1), the gate proves it catches violations (US2), and the existing codebase is verified fully
compliant right now (US3).

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation and documentation.

- [X] T023 [P] Add a short note to the "Quality gates" section of `README.md` describing the Google-style docstring requirement (public + private symbols in `src/`, `tests/` exempt) and linking `specs/008-google-style-docstrings/contracts/docstring-style.md`
- [X] T024 Run every scenario in `quickstart.md` end-to-end (full repo passes clean, `pydoc`/`help()` readability, missing-docstring gate failure, mismatched-Args/Returns gate failure, `tests/` exemption) and confirm expected outcomes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately. T001 (gate configuration) is the one
  prerequisite every other phase relies on for real-time verification.
- **Foundational (Phase 2)**: Empty — no shared infrastructure beyond Phase 1 exists for this
  feature.
- **User Story 1 (Phase 3)**: Depends on Phase 1 (so `poe lint` gives real-time feedback while
  writing docstrings, rather than a blind pass). The MVP.
- **User Story 2 (Phase 4)**: Depends on Phase 1 (the mechanism it tests must exist). Independent of
  Phase 3's content.
- **User Story 3 (Phase 5)**: Depends on Phase 1 AND Phase 3 (it verifies the retrofit Phase 3
  performs).
- **Polish (Phase 6)**: After the desired stories are complete.

### User Story Dependencies

- **US1 (P1)**: Depends only on Phase 1 (Setup).
- **US2 (P2)**: Depends only on Phase 1 (Setup); independent of US1's specific file content.
- **US3 (P3)**: Depends on both Phase 1 (Setup) and US1 (the retrofit content it verifies).

### Within Each User Story

- **US1**: All 16 file tasks (T002–T017) are mutually independent — different files, no shared
  state.
- **US2**: Fixtures (T019, T020) before the self-test that consumes them (T021); the config
  assertion (T018) is independent of both.
- **US3**: A single verification task with a hard dependency on US1's content existing.

### Parallel Opportunities

- **US1**: All of T002–T017 can run in parallel — 16 independent files.
- **US2**: T018, T019, T020 can all run in parallel; T021 waits on T019/T020.
- **Polish**: T023 parallel to T024.

---

## Parallel Example: User Story 1 (all 16 files)

```bash
# Every file below is independent — no shared state, no import-order dependency:
Task: "Add module docstring to src/wh40k_cheatsheet/__init__.py"
Task: "Add module + function docstrings to src/wh40k_cheatsheet/cli.py"
Task: "Add module + function docstrings to src/wh40k_cheatsheet/logging_setup.py"
Task: "Add module + class + function docstrings to src/wh40k_cheatsheet/pipeline.py"
# ...and so on for all 16 files in T002–T017
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001) — gate configured, all existing findings now visible.
2. Complete Phase 3: User Story 1 (T002–T017) — every file documented.
3. **STOP and VALIDATE**: `uv run python -m pydoc wh40k_cheatsheet.pipeline` shows real,
   Google-style docstrings for every symbol.
4. Demonstrable MVP — the codebase is self-explaining via `pydoc`/`help()`.

### Incremental Delivery

1. Setup (T001) → the gate exists and immediately surfaces the current 55/65 findings.
2. US1 (T002–T017) → every file documented (MVP!) → validate via `pydoc` → demo.
3. US2 (T018–T021) → the enforcement mechanism is proven with seeded fixtures → validate → demo.
4. US3 (T022) → formal zero-violations confirmation → validate → demo.
5. Polish (T023–T024) → docs + full quickstart validation.

---

## Notes

- [P] = different files, no dependencies. All 16 US1 file tasks qualify — this is the most
  parallelizable phase in the project so far.
- [Story] label maps each task to its user story for traceability.
- T021 (US2's self-test) must fail against `bad_docstring_example.py` and pass against
  `good_docstring_example.py` — both are the actual test signal, not just "test exists."
- No new dependency is introduced anywhere in this feature — `pylint.extensions.docparams` ships
  with the already-installed `pylint`.
- Commit after each task or logical group; stop at any checkpoint to validate a story independently.
