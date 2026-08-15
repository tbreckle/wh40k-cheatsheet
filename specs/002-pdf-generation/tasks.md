---

description: "Task list for PDF Generation implementation"
---

# Tasks: PDF Generation from Templated Source Files

**Input**: Design documents from `/specs/002-pdf-generation/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/config-schema.md, contracts/generate-command.md, quickstart.md

**Tests**: Test tasks ARE included — the spec defines validation scenarios and the constitution's
Testing Standards are non-negotiable.

**Organization**: Grouped by user story so each is an independently testable increment.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1, US2, US3
- Exact file paths are included. Builds on the Python 3.12+/uv toolchain from feature 001.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Runtime dependencies, package skeleton, and native-library prerequisites.

- [X] T001 Add runtime dependencies (pydantic v2, pyyaml, jinja2, weasyprint) to `pyproject.toml` and regenerate `uv.lock` via `uv sync`
- [X] T002 [P] Create the package skeleton with `__init__.py` files: `src/wh40k_cheatsheet/config/`, `content/`, `render/`, `pdf/`, plus empty `src/wh40k_cheatsheet/cli.py` and `src/wh40k_cheatsheet/pipeline.py`
- [X] T003 Document WeasyPrint native libraries (Pango, cairo, GDK-PixBuf, HarfBuzz) as a prerequisite in `README.md` and install them in the CI job in `.github/workflows/quality.yml` (per research.md §5)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Config model + loader (used by every story and by `list`) and shared test fixtures.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 [P] Create shared test fixtures under `tests/fixtures/`: a sample `project.yaml` (edition `10e` with `en` + `de`), `templates/base.html.j2`, and `editions/10e/en/` + `editions/10e/de/` content (strings + an HTML fragment) — **adapted**: no synthetic test fixture was created; real production content was used instead — repo-root `project.yaml` (edition `11e`), `templates/cheatsheet.html.j2`, and `editions/11e/2026-08-01-00/{en,de}/content.yaml` (transcribed from the actual cheat sheet), which exercises the same resolver/loader/renderer paths end-to-end
- [X] T005 [P] Define Pydantic v2 config models `ProjectConfig`, `Edition`, `LanguageEntry` (with `extra="forbid"`, non-empty-languages validator, language-code pattern) in `src/wh40k_cheatsheet/config/models.py` (data-model.md; contracts/config-schema.md C1–C7)
- [X] T006 Implement the config loader (PyYAML `safe_load` → Pydantic validation, raising clear file/field-located errors) in `src/wh40k_cheatsheet/config/loader.py` (depends on T005; FR-008)
- [X] T007 Write unit tests for config models + loader covering valid config and each invalid case C1–C7 in `tests/unit/test_config.py` — implemented 2026-08-14: 14 tests covering C1–C6 (C7 is a schema-shape property with no field to test)

**Checkpoint**: Config can be loaded and validated; fixtures exist. Pipeline not yet built.

---

## Phase 3: User Story 1 - Generate a cheatsheet PDF from source files (Priority: P1) 🎯 MVP

**Goal**: One command renders a template to HTML then converts it to a valid PDF for one edition and
one language.

**Independent Test**: `generate --edition 10e --language en` yields `out/10e/en.html` and a valid,
non-empty `out/10e/en.pdf` whose content matches the source strings/HTML in the template's layout.

### Tests for User Story 1 ⚠️

- [X] T008 [P] [US1] Golden-HTML render test (template + fixed context → expected HTML snapshot) in `tests/golden/` and `tests/unit/test_html_renderer.py` — implemented 2026-08-14: dedicated minimal fixture template (`tests/unit/fixtures/golden_template.html.j2`), decoupled from the real, frequently-changing cheatsheet template
- [X] T009 [P] [US1] Integration test: generate one (`10e`, `en`) and assert a retained HTML file plus a valid, non-empty PDF are produced in `tests/integration/test_generate_single.py` — implemented 2026-08-14: adapted to the real `11e` edition, same as prior adapted tasks

### Implementation for User Story 1

- [X] T010 [P] [US1] Implement the content resolver (convention `editions/<edition-id>/<lang-code>/` → `StringCatalog` + `HtmlFragment`s; missing file/key raises a clear error) in `src/wh40k_cheatsheet/content/resolver.py` (FR-019) — **adapted**: content is resolved as a single `content.yaml` per (edition, revision, language) providing the full Jinja2 render context directly, rather than separate `StringCatalog`/`HtmlFragment` types; missing file raises `ContentError`
- [X] T011 [P] [US1] Implement the Jinja2 HTML renderer (Environment with template loader from `templates/`, `autoescape` for HTML, `StrictUndefined`, explicit `safe` injection for trusted fragments) in `src/wh40k_cheatsheet/render/html_renderer.py` (research.md §4)
- [X] T012 [P] [US1] Implement the WeasyPrint PDF converter (HTML string/file → PDF) in `src/wh40k_cheatsheet/pdf/weasyprint_pdf.py` (research.md §5)
- [X] T013 [US1] Implement the pipeline orchestrator (load config → resolve template via language-override-else-edition-default → resolve content → render HTML → convert PDF → return `GeneratedDocument`) in `src/wh40k_cheatsheet/pipeline.py` (depends on T010–T012; FR-002, FR-017)
- [X] T014 [US1] Implement the CLI `generate --edition <id> --language <code>` and `list` in `src/wh40k_cheatsheet/cli.py`, and wire a console entrypoint + poe task in `pyproject.toml` (depends on T013; contracts/generate-command.md; FR-013, SC-007)
- [X] T015 [US1] Add fail-loud error handling across the pipeline (missing/malformed config, missing template, missing content, unknown edition/language) producing clear messages with no partial/corrupt PDF, in `src/wh40k_cheatsheet/pipeline.py` and the resolver/loader (FR-008, SC-005) — verified manually against unknown edition/revision/language and missing-content-file cases, all exit 1 with clear messages

**Checkpoint**: MVP — a single-command, HTML-then-PDF generator with the self-contained fixture.

---

## Phase 4: User Story 2 - Produce the document in multiple languages (Priority: P2)

**Goal**: Generate one localized PDF per supported language in a single run, with per-language
template overrides and reported (never silent) missing strings.

**Independent Test**: Generating all languages of `10e` yields exactly one PDF per language with the
same layout; a `de` template override is applied; a missing `de` string is reported with context.

### Tests for User Story 2 ⚠️

- [X] T016 [P] [US2] Integration test: `generate --edition 10e` (no `--language`) produces exactly one PDF per declared language in `tests/integration/test_generate_all_languages.py` (FR-005, SC-003) — implemented 2026-08-14
- [X] T017 [P] [US2] Unit test: language-level `template` override wins over the edition template in `tests/unit/test_template_resolution.py` (FR-017) — implemented 2026-08-14
- [X] T018 [P] [US2] Integration test: a referenced string missing from the `de` catalog fails with a message naming the key, language, and edition, emitting no PDF, in `tests/integration/test_missing_string.py` (FR-009) — implemented 2026-08-14: writing this test surfaced a real FR-009 gap — `RenderError` for an unresolved content reference didn't name the edition/revision/language (only `ContentError` for a missing file already did); fixed in `pipeline.py._generate_one` by wrapping `RenderError` with the `[edition/revision/language]` prefix, matching the existing log-line convention

### Implementation for User Story 2

- [X] T019 [US2] Implement the all-languages generation path (when `--language` is omitted, iterate the edition's declared languages, producing one `GeneratedDocument` each) in `src/wh40k_cheatsheet/cli.py` and `src/wh40k_cheatsheet/pipeline.py` (FR-005) — verified: `generate --edition 11e` produces one PDF per declared language (en, de) in one run
- [X] T020 [P] [US2] Ensure unresolved string references and missing HTML fragments are reported with language + edition + key context in `src/wh40k_cheatsheet/content/resolver.py` and `src/wh40k_cheatsheet/render/html_renderer.py` (FR-009) — missing content file reported with edition/revision/language/path; missing template key reported via Jinja2 `StrictUndefined`

**Checkpoint**: US1 and US2 both work — single-language and all-languages generation.

---

## Phase 5: User Story 3 - Manage multiple editions (revisions) (Priority: P3)

**Goal**: Generate a specifically requested edition and keep past editions reproducible in content.

**Independent Test**: Generating a chosen edition reflects that edition's content; regenerating an
earlier edition produces content-equivalent output across runs.

### Tests for User Story 3 ⚠️

- [X] T021 [P] [US3] Integration test: selecting a specific edition renders that edition's content, and an unknown edition fails listing available editions, in `tests/integration/test_edition_selection.py` (FR-006, Edge Cases) — implemented 2026-08-14
- [X] T022 [P] [US3] Reproducibility test: regenerating the same (edition, language) twice yields content-equivalent PDFs in `tests/integration/test_reproducible.py` (FR-010, FR-011, SC-004) — implemented 2026-08-14: byte-identical HTML and PDF, not just content-equivalent

### Implementation for User Story 3

- [X] T023 [US3] Ensure edition selection resolves the correct edition's template + content set and errors (listing available editions) on an unknown edition, in `src/wh40k_cheatsheet/pipeline.py` and `src/wh40k_cheatsheet/cli.py` (FR-006, FR-012) — verified: unknown edition fails with `Available: 11e`
- [X] T024 [P] [US3] Implement deterministic output — pin/normalize WeasyPrint document metadata and avoid wall-clock timestamps so runs are content-equivalent — in `src/wh40k_cheatsheet/pdf/weasyprint_pdf.py` (FR-010/FR-011/SC-004; research.md §7) — verified WeasyPrint 69.0 embeds no wall-clock metadata; regenerated PDF is byte-identical (`cmp` confirmed) without extra pinning code needed
- [X] T025 [P] [US3] Add a second fixture edition (e.g., `9e`) under `tests/fixtures/editions/9e/` and its entry in the fixture `project.yaml` to exercise multi-edition generation — implemented 2026-08-14 in `tests/integration/test_multi_edition.py`: a synthetic second edition is added only inside a `tmp_path` copy of the real project (never committed to the real repo), proving multi-edition discovery/selection/isolation without fabricating permanent fake content

**Checkpoint**: All three stories independently functional; editions selectable and reproducible.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation and finishing touches.

- [X] T026 Run every scenario in `quickstart.md` end-to-end (list, single, all-languages, override, missing-string, invalid-config, unknown-edition, reproducibility) and confirm expected outcomes — all verified manually against the real `11e` content/config
- [X] T027 [P] Confirm a single (edition, language) PDF generates in under ~10s for the fixture (SC-006) and record the measured time in `README.md` — measured ~5.9s
- [X] T028 [P] Update `README.md` with usage for `generate`/`list`, a link to the config schema contract, and the output layout (`out/<edition-id>/<lang-code>.{html,pdf}`) — output layout documented as `out/<edition-id>/<revision-id>/<lang-code>.{html,pdf}` per the feature-003 revision extension

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories (config loader + fixtures).
- **US1 (Phase 3)**: Depends on Foundational. The MVP.
- **US2 (Phase 4)**: Depends on US1's pipeline/CLI (`generate`) existing.
- **US3 (Phase 5)**: Depends on US1's pipeline; extends it with multi-edition + reproducibility.
- **Polish (Phase 6)**: Depends on the desired stories being complete.

### User Story Dependencies

- **US1 (P1)**: Independent once Foundational is done.
- **US2 (P2)**: Reuses US1's pipeline (all-languages loop + reporting).
- **US3 (P3)**: Reuses US1's pipeline (edition selection + deterministic PDF).

### Within Each User Story

- Tests before implementation (T008/T009 before T010–T015; T016–T018 before T019–T020; T021/T022 before T023–T025).
- Content resolver / renderer / PDF converter (T010–T012) before the pipeline (T013) before the CLI (T014).

### Parallel Opportunities

- **Setup**: T002 is independent of T001/T003.
- **Foundational**: T004 (fixtures) and T005 (models) are different files → parallel; T006 depends on T005.
- **US1**: T008/T009 (tests) parallel; T010/T011/T012 are three different modules → parallel; T013 waits on them.
- **US2**: T016/T017/T018 parallel; T020 parallel to T019 (different files).
- **US3**: T021/T022 parallel; T024 and T025 parallel to T023 (different files).
- **Polish**: T027/T028 parallel.
- `pyproject.toml`-touching tasks (T001, T014) run sequentially.

---

## Parallel Example: User Story 1 core modules

```bash
# After the pipeline's dependencies are stubbed, the three engine modules are independent:
Task: "Implement content resolver in src/wh40k_cheatsheet/content/resolver.py"
Task: "Implement Jinja2 HTML renderer in src/wh40k_cheatsheet/render/html_renderer.py"
Task: "Implement WeasyPrint PDF converter in src/wh40k_cheatsheet/pdf/weasyprint_pdf.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003).
2. Complete Phase 2: Foundational (T004–T007) — CRITICAL, blocks all stories.
3. Complete Phase 3: User Story 1 (T008–T015).
4. **STOP and VALIDATE**: `generate --edition 10e --language en` produces valid HTML + PDF; render golden test passes.
5. Demonstrable MVP — a working templated PDF generator.

### Incremental Delivery

1. Setup + Foundational → config + fixtures ready.
2. US1 → single-document generation (MVP!) → validate → demo.
3. US2 → multi-language, overrides, missing-string reporting → validate → demo.
4. US3 → multi-edition + reproducibility → validate → demo.
5. Polish → quickstart + performance + docs.

---

## Notes

- [P] = different files, no dependencies. Tasks sharing a file (e.g., `pyproject.toml`, `pipeline.py`) run serially.
- [Story] label maps each task to its user story for traceability.
- Tests (T007–T009, T016–T018, T021–T022) must fail before their implementation lands.
- WeasyPrint requires native libraries — ensure T003 is done before running any PDF-producing test.
- Commit after each task or logical group; stop at any checkpoint to validate a story independently.
