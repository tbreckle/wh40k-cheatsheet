---

description: "Task list for Skip Cheat Sheet Sections on Generation"
---

# Tasks: Skip Cheat Sheet Sections on Generation

**Input**: Design documents from `/specs/015-skip-sheet-sections/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-skip-flags.md, contracts/section-marker-block.md, quickstart.md

**Tests**: Included. Constitution principle II (Testing Standards) is NON-NEGOTIABLE and requires
every new feature to ship with tests covering expected behavior plus at least one boundary or
failure case.

**Organization**: Grouped by user story so each is an independently testable increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1, US2, US3 (from spec.md)
- Paths are repository-relative (single project: `src/`, `tests/`, `editions/`, `templates/`, `docs/`)

## Reference: section vocabulary (data-model.md §1)

| Canonical order | Section id | CLI flag | 11e `en` signature in HTML | 11e `de` signature in HTML |
|---|---|---|---|---|
| 1 | `core-rules` | `--skip-core-rules` | `1. COMMAND PHASE (08)` | `1. BEFEHLSPHASE (08)` |
| 2 | `core-abilities` | `--skip-core-abilities` | `CORE ABILITIES` (glossary `<h2>`) | `KERNFÄHIGKEITEN` |
| 3 | `datasheet-characteristics` | `--skip-datasheet-characteristics` | `DATASHEET CHARACTERISTICS` | `DATENBLATT-KENNWERTE` |
| 4 | `core-stratagems` | `--skip-core-stratagems` | `STRATAGEMS`, `USING STRATAGEMS`, `class="stratagem"` | `GEFECHTSOPTIONEN`, `GEFECHTSOPTIONEN VERWENDEN`, `class="stratagem"` |

Output stem rule (data-model.md §6, contracts/cli-skip-flags.md O2):
`<lang>` + (`-no-` + actually-omitted ids in canonical order joined by `-`) + (`-print` if print-friendly).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Capture the pre-feature output so "no flags → identical output" can be checked by hand later.

- [X] T001 Before changing any code or content, run `uv run wh40k-cheatsheet generate --edition 11e --print-friendly` and `uv run wh40k-cheatsheet generate --edition 10e --print-friendly`, then copy `out/11e/2026-06-01-00/*.html` and `out/10e/2026-06-16-00/*.html` to a scratch directory outside the repository (e.g. `/tmp/baseline-015/`) as the byte-identity reference for quickstart.md §2

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The section vocabulary, the transparent `section` marker, marker validation, the pure
omission/naming functions, and markers in every shipped content file. Every user story depends on
all of this.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

### Tests for Foundational ⚠️

> Write these first; confirm they fail before T006–T012.

- [X] T002 [P] Create `tests/unit/test_sections.py` with tests for: `SECTION_IDS == ("core-rules", "core-abilities", "datasheet-characteristics", "core-stratagems")`; `validate_section_markers(blocks)` returns `[]` for a valid document (marker first, unique known ids), returns `[]` for a document with zero markers (contract V4), and returns a non-empty list of messages naming the problem for each of: unknown `id`, missing `id`, duplicate `id`, first block not a `section` marker (contract V1–V3); `has_section_markers()` true/false; `invalid_section_ids(frozenset({"core-rules", "bogus"})) == ("bogus",)`
- [X] T003 Extend `tests/unit/test_sections.py` (after T002, same file) with tests for `omit_sections(blocks, selection)` per data-model.md §5: empty selection returns equal blocks and `omitted == ()`; a present+selected section's whole region is removed **including its marker and its own `page_break`/`column_reset`**; an absent+selected section removes nothing and is not in `omitted` (FR-009); two selected sections yield `omitted` in canonical order regardless of set iteration order; unselected sections keep their marker; the input list and block dicts are not mutated. Tests for `has_content(blocks)`: `False` for `[]` and for lists holding only `section`/`page_break`/`column_reset` blocks, `True` otherwise. Tests for `output_stem()` covering every row of research.md §7's table, e.g. `output_stem("en", ("core-rules", "core-stratagems"), print_friendly=True) == "en-no-core-rules-core-stratagems-print"` and `output_stem("de", (), print_friendly=False) == "de"`. Add a combinatorial test (FR-005 empty columns, SC-002): for each shipped content file (`11e/en`, `11e/de`, `10e/de`, loaded via `resolve_content`) and each of the 15 non-empty subsets of `SECTION_IDS`, when `has_content(result.blocks)`, assert every `Segment` from `group_by_breaks(result.blocks)` holds at least one non-marker block (no empty column container), and that the segment count never exceeds the full sheet's
- [X] T004 [P] Extend `tests/unit/test_page_breaks.py` with tests (reuse its `_block`/`_break` helpers and add a `_section(id)` helper returning `{"type": "section", "id": id}`) asserting: a `section` marker between two blocks does not split them (one segment); a leading `section` marker produces no empty segment; `[_break(), _section("x"), _block("a")]` still yields one segment with `break_type` unchanged from `[_break(), _block("a")]`; a list of only `section` markers yields no segments; no `Segment.blocks` ever contains a `section` block (contract M1)
- [X] T005 [P] Create `tests/unit/test_content_resolver_sections.py` that writes a `content.yaml` into `tmp_path / "11e" / "2026-01-01-00" / "en"` and calls `resolve_content(tmp_path, "11e", "2026-01-01-00", "en")`, asserting: a valid marker layout loads; a document with zero markers loads (V4); a duplicate id, an unknown id, and a block before the first marker each raise `ContentError` whose message contains the content file path and the offending id/position (contract V1–V3)

### Implementation for Foundational

- [X] T006 Create `src/wh40k_cheatsheet/content/sections.py` (module docstring; Google-style docstrings with `Args:`/`Returns:` on every public name, per the `008` docstring gate; full type annotations) containing: `SECTION_MARKER_TYPE = "section"`; `SECTION_IDS: tuple[str, ...]` in canonical order; frozen `@dataclass(frozen=True, slots=True) class OmissionResult` with `blocks: list[dict[str, Any]]` and `omitted: tuple[str, ...]`; `validate_section_markers(blocks) -> list[str]`; `has_section_markers(blocks) -> bool`; `invalid_section_ids(selection: frozenset[str]) -> tuple[str, ...]` (sorted); `omit_sections(blocks, selection) -> OmissionResult` (pure; walks blocks, tracking the current region's id, dropping every block of a selected region including its marker); `has_content(blocks) -> bool`; `output_stem(language: str, omitted: tuple[str, ...], *, print_friendly: bool) -> str`. It MUST NOT import from `content/resolver.py` or `pipeline.py` (the resolver imports this module), so it raises nothing. Callers turn returned problems into `ContentError`/`PipelineError` (makes T002/T003 pass)
- [X] T007 In `group_by_breaks()` in `src/wh40k_cheatsheet/render/html_renderer.py`, import `SECTION_MARKER_TYPE` from `wh40k_cheatsheet.content.sections` and add a branch so a block whose `type` equals it is skipped with `continue`: not appended to `current`, not flushing a segment, not touching `pending`. Update the docstring to say `section` markers are dropped without splitting (contract M1; depends on T006; makes T004 pass)
- [X] T008 In `resolve_content()` in `src/wh40k_cheatsheet/content/resolver.py`, when `document["blocks"]` is a list, call `validate_section_markers(blocks)`; if it returns problems, raise `ContentError(f"{content_path}: invalid section markers: " + "; ".join(problems))`. Documents with zero markers stay valid. Update the docstring's `Raises:` (contract V1–V4; depends on T006; makes T005 pass)
- [X] T009 Create `tests/integration/test_section_markers_shipped_content.py` that, for every shipped (edition, latest revision, language) - discover them the same way `tests/integration/test_glossary_order_cross_language.py` does (`discover_revisions(...).latest()` + `resolve_content`), covering `11e/en`, `11e/de`, `10e/de` - asserts: content resolves (V1–V3 pass); `has_section_markers()` is true (S1, SC-006); the set of marker ids is all four for `11e/en` and `11e/de` and `{"core-rules", "core-abilities", "core-stratagems"}` for `10e/de`; and `render_html(TEMPLATES_ROOT, "cheatsheet.html.j2", content)` is **byte-identical** to rendering a deep copy with every `section` block removed from `document.blocks` (contract M2, FR-006). Confirm it fails before T010–T012 (depends on T006–T008)
- [X] T010 [P] Add `section` markers to `editions/11e/2026-06-01-00/en/content.yaml` (each marker is `- type: section` + `id: <id>` at block indentation): `core-rules` as the first entry of `document.blocks`, before the `1. COMMAND PHASE (08)` phase; `core-abilities` immediately before the `page_break` under the `# ===== PAGE 3 - DATASHEET CHARACTERISTICS =====` comment (~line 303); `datasheet-characteristics` immediately before the `glossary` titled `DATASHEET CHARACTERISTICS` (~line 438); `core-stratagems` immediately before the `page_break` under the `# ===== PAGE 4 - STRATAGEMS =====` comment (~line 478) (contracts/section-marker-block.md A1–A3 and placement table)
- [X] T011 [P] Add `section` markers to `editions/11e/2026-06-01-00/de/content.yaml`: `core-rules` first, before `1. BEFEHLSPHASE (08)`; `core-abilities` immediately before the `page_break` preceding the `KERNFÄHIGKEITEN` glossary (~line 311); `datasheet-characteristics` immediately before the `glossary` titled `DATENBLATT-KENNWERTE` (~line 452); `core-stratagems` immediately before the `page_break` under `# ===== SEITE 3 - GEFECHTSOPTIONEN =====` (~line 510)
- [X] T012 [P] Add `section` markers to `editions/10e/2026-06-16-00/de/content.yaml`: `core-rules` first, before `1. BEFEHLSPHASE`; `core-abilities` immediately before the `column_reset` preceding the `KERNFÄHIGKEITEN` glossary (~line 211); **no** `datasheet-characteristics` marker (this sheet has no such section, A4); `core-stratagems` immediately before the `page_break` under `# ===== SEITE 3 - GEFECHTSOPTIONEN =====` (~line 343). After T010–T012, T009 and the full existing suite (`uv run pytest`) must pass unchanged

**Checkpoint**: Markers exist in every shipped file, are validated on load, and are invisible in
rendered output. No user-visible behavior has changed yet.

---

## Phase 3: User Story 1 - Generate a sheet without one section (Priority: P1) 🎯 MVP

**Goal**: `generate --skip-<section>` writes a partial sheet, `<lang>-no-<id>.pdf`, alongside the
untouched full sheet, with that section fully absent and no blank pages.

**Independent Test**: `uv run wh40k-cheatsheet generate --edition 11e --language en --skip-core-stratagems`
writes `out/11e/2026-06-01-00/en-no-core-stratagems.pdf` with no stratagem content and no blank page,
and leaves `en.pdf` unchanged.

### Tests for User Story 1 ⚠️

> Write these first; confirm they fail before T015–T017.

- [X] T013 [P] [US1] Create `tests/integration/test_skip_sections_pdf.py` with a `_project_root(tmp_path)` helper copying `project.yaml`, `editions/`, `templates/`, `images/` into `tmp_path / "project"` (as in `tests/integration/test_print_friendly_pdf.py`) and a `_paths(root)` helper. Add tests calling `generate(config, paths, "11e", language="en", skip_sections=frozenset({section_id}))`, parametrized over all four section ids, asserting: `doc.pdf_path.name == f"en-no-{section_id}.pdf"` and `doc.html_path.name == f"en-no-{section_id}.html"`; `doc.omitted_sections == (section_id,)`; the written HTML contains none of that section's 11e `en` signatures from the reference table and all other sections' signatures (FR-003/FR-004); every page of the rendered PDF has at least one text box inside a `.sheet` element (walk boxes as `_all_pages_boxes` does; running header/footer margin boxes don't count) (FR-005/SC-002). Add: the skip-`core-stratagems` PDF has fewer pages than the full sheet; the skip-`core-rules` PDF's first page contains `CORE ABILITIES`; generating the full sheet first, then a skip, leaves `en.pdf`/`en.html` bytes unchanged (SC-007, O1); `generate(...)` without `skip_sections` still writes `en.pdf` with `omitted_sections == ()` (C4); `generate(..., skip_sections=frozenset({"stratagems"}))` raises `PipelineError` whose message names `stratagems` and lists the four valid ids (F2); with every `section` block stripped from a tmp copy of `editions/11e/2026-06-01-00/en/content.yaml`, `generate(..., language="en", skip_sections=frozenset({"core-rules"}))` raises `ContentError` whose message contains "no section markers" and that content file's path, while the same call without `skip_sections` succeeds (F4, V4)
- [X] T014 [P] [US1] Create `tests/integration/test_skip_sections_cli.py` (same `_project_root` helper) with tests calling `wh40k_cheatsheet.cli.main([...])`: `["--project-root", root, "generate", "--edition", "11e", "--language", "en", "--skip-core-stratagems"]` exits `0`, prints exactly one stdout line ending in `en-no-core-stratagems.pdf`, and that file exists (C1, C6); the same command without the flag prints exactly one line ending in `en.pdf` (C4); `main(["generate", "--help"])` raises `SystemExit(0)` and the captured stdout contains all four `--skip-*` flag names (C5, FR-015); `main([... "generate", "--edition", "11e", "--skip-stratagems"])` raises `SystemExit` with code `2`, captured stderr contains all four valid `--skip-*` flag names, and no `out/` directory is created (F1, FR-010); a non-skip unknown flag (`--bogus`) still raises `SystemExit(2)` with stderr containing "unrecognized arguments: --bogus" and no `--skip-*` listing (existing behavior unchanged)

### Implementation for User Story 1

- [X] T015 [US1] In `src/wh40k_cheatsheet/pipeline.py`, add `omitted_sections: tuple[str, ...] = ()` as the last field of `GeneratedDocument` and document it in the class docstring's `Attributes:` ("ids actually omitted, canonical order; empty when nothing was omitted") (data-model.md §7, O6)
- [X] T016 [US1] In `src/wh40k_cheatsheet/pipeline.py`: add keyword `skip_sections: frozenset[str] = frozenset()` to `generate()` and `_generate_one()`. In `generate()`, before resolving anything, call `invalid_section_ids(skip_sections)`; if non-empty, raise `PipelineError` naming the invalid ids and listing `SECTION_IDS` (F2). Append ` [skip: <ids in SECTION_IDS order, comma-separated>]` to the existing INFO "generating edition …" log line only when `skip_sections` is non-empty. In `_generate_one()`, after `resolve_content`: if `skip_sections` and not `has_section_markers(blocks)`, build `content_path = paths.editions_root / edition_id / str(revision.id) / language / CONTENT_FILENAME` (import `CONTENT_FILENAME` from `wh40k_cheatsheet.content.resolver`) and raise `ContentError(f"{content_path}: content has no section markers; cannot skip sections")` (F4 - raised here, not in `sections.py`, to avoid an import cycle). Then `result = omit_sections(blocks, skip_sections)`, render with `context = {**context, "document": {**context["document"], "blocks": result.blocks}}`, use `filename_stem=output_stem(language, result.omitted, print_friendly=False)` for the standard pair and `output_stem(language, result.omitted, print_friendly=True)` for the print-friendly pair, and set `omitted_sections=result.omitted`. Update docstrings (`Args:`/`Raises:`). With an empty `skip_sections`, stems must stay exactly `language` / `f"{language}-print"` (C4) (depends on T015; makes T013 pass)
- [X] T017 [US1] In `src/wh40k_cheatsheet/cli.py`: import `SECTION_IDS` from `wh40k_cheatsheet.content.sections`; in `build_parser()`, after the `--print-friendly` argument on `generate_parser`, loop over `SECTION_IDS` adding `f"--skip-{section_id}"` with `action="store_true"` and help `f"Omit the '{section_id}' section from the generated sheet(s)"`. In `_cmd_generate()`, build `skip_sections = frozenset(sid for sid in SECTION_IDS if getattr(args, "skip_" + sid.replace("-", "_")))` and pass `skip_sections=skip_sections` to `generate(...)`. In `main()`, replace `args = parser.parse_args(argv)` with `args, unknown = parser.parse_known_args(argv)`; if `unknown` is non-empty, call `parser.error(f"unrecognized arguments: {' '.join(unknown)} (valid section flags: {', '.join('--skip-' + s for s in SECTION_IDS)})")` when any entry starts with `--skip-`, else `parser.error(f"unrecognized arguments: {' '.join(unknown)}")` (argparse's own message, exit code `2`) - before `configure_logging` or dispatch, so nothing is resolved or written. This is needed because argparse reports unknown subcommand arguments via the top-level parser, whose usage line doesn't list `generate`'s flags (F1, FR-010). Leave the `package` subparser untouched (C1–C3, C5, C7; depends on T016; makes T014 pass)

**Checkpoint**: MVP. Any single section can be skipped from the CLI; partial sheets sit beside
untouched full sheets with no blank pages.

---

## Phase 4: User Story 2 - Omit several sections in one run (Priority: P2)

**Goal**: Several `--skip-*` flags combine into one partial sheet with an order-independent name,
and any run that would leave a sheet empty fails before writing anything.

**Independent Test**: `--skip-core-rules --skip-core-stratagems` writes only
`en-no-core-rules-core-stratagems.pdf` with just the two glossaries. Passing all four flags exits `1`
and writes nothing.

### Tests for User Story 2 ⚠️

> Write these first; confirm the empty-sheet tests fail before T020.

- [X] T018 [P] [US2] Extend `tests/integration/test_skip_sections_pdf.py` (after T013, same file): `skip_sections=frozenset({"core-rules", "core-stratagems"})` → `pdf_path.name == "en-no-core-rules-core-stratagems.pdf"`, `omitted_sections == ("core-rules", "core-stratagems")`, HTML contains only the `CORE ABILITIES` and `DATASHEET CHARACTERISTICS` signatures (US2 scenario 1, SC-005); skipping three sections leaves only the fourth's signature and no blank page (US2 scenario 2)
- [X] T019 [P] [US2] Extend `tests/integration/test_skip_sections_cli.py` (after T014, same file): `--skip-core-stratagems --skip-core-rules` and `--skip-core-rules --skip-core-stratagems` each write exactly one new file, `en-no-core-rules-core-stratagems.pdf` (FR-012 order independence); all four flags on `--edition 11e` exit `1`, stderr contains "no content", and `out/` does not exist afterwards (F3, FR-011); `--edition 10e --skip-core-rules --skip-core-abilities --skip-core-stratagems` exits `1` with nothing written (FR-011's extended case); **fail before any write for any language**: in the tmp project, rewrite `editions/11e/2026-06-01-00/de/content.yaml` so its blocks are only a `core-rules` region (marker plus one paragraph), run `generate --edition 11e --skip-core-rules` (no `--language`), and assert exit `1` and that neither `en*.pdf` nor `de*.pdf` exists under `out/11e/` (F3)

### Implementation for User Story 2

- [X] T020 [US2] In `src/wh40k_cheatsheet/pipeline.py`, restructure generation into two passes so no file is written until every language is known to be non-empty: split `_generate_one()` into `_prepare_one(config, paths, edition_id, revision, language, *, skip_sections) -> _PreparedDocument` (a small frozen dataclass holding `language`, `template_name`, `stage_context`, the filtered `context`, and `omitted`; performs template resolution, `resolve_content`, the F4 marker check, `omit_sections`, and raises `PipelineError(f"[{stage_context}] skipping {', '.join(ordered skip ids)} would leave no content to generate")` when `not has_content(result.blocks)`) and `_write_one(paths, prepared, *, print_friendly) -> GeneratedDocument` (renders/writes the standard and optional print-friendly pairs with `output_stem`). Make `generate()` call `_prepare_one` for **all** languages first, then `_write_one` for each. Keep log messages, their order per language, and no-flag output identical to before; update docstrings (F3, research.md §6; depends on T016; makes T019's empty-sheet tests pass)

**Checkpoint**: US1 and US2 both work. Any combination of flags produces one deterministic file,
and impossible combinations fail cleanly with nothing written.

---

## Phase 5: User Story 3 - Consistent behavior across languages, editions, and variants (Priority: P3)

**Goal**: The same omission applies to every language in the run and to the print-friendly
variant, and skipping a section an edition doesn't have is a harmless no-op.

**Independent Test**: `generate --edition 11e --print-friendly --skip-datasheet-characteristics`
writes four `…-no-datasheet-characteristics[-print].pdf` files (en/de), none containing the section.
`generate --edition 10e --skip-datasheet-characteristics` writes plain `de.pdf`.

### Tests for User Story 3 ⚠️

- [X] T021 [P] [US3] Extend `tests/integration/test_skip_sections_pdf.py` (after T018, same file): `generate(config, paths, "11e", print_friendly=True, skip_sections=frozenset({"datasheet-characteristics"}))` returns two documents whose `pdf_path`/`print_pdf_path` names are `en-no-datasheet-characteristics.pdf`, `en-no-datasheet-characteristics-print.pdf`, `de-no-datasheet-characteristics.pdf`, `de-no-datasheet-characteristics-print.pdf`; none of those HTML files contains `DATASHEET CHARACTERISTICS` or `DATENBLATT-KENNWERTE`; the `<article class="cheatsheet">…</article>` region is identical between each standard and print-friendly partial HTML (FR-008, O5); `generate(config, paths, "10e", skip_sections=frozenset({"datasheet-characteristics"}))` yields `pdf_path.name == "de.pdf"`, `omitted_sections == ()`, and HTML byte-identical to `generate(config, paths, "10e")` (FR-009, O4)
- [X] T022 [P] [US3] Create `tests/integration/test_skip_sections_cross_language.py` rendering real `11e` content for `en` and `de` through `generate(...)` into a tmp project, parametrized over all four section ids: that section's language-specific signatures (reference table) are absent and the other three sections' signatures are present, in both languages (FR-007, US3 scenario 1)

### Implementation for User Story 3

- [X] T023 [US3] Run T021 and T022. No new implementation is expected, since T016/T020 already pass `omitted` into both stems and apply the selection per language. If a check fails, fix the print-friendly stem or the per-language propagation in `_write_one()`/`_prepare_one()` in `src/wh40k_cheatsheet/pipeline.py` without changing no-flag output (depends on T020)

**Checkpoint**: All three stories independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, release-path regression coverage, and end-to-end validation.

- [X] T024 [P] Update the header doc comment in `templates/cheatsheet.html.j2`: add `section` to the `<block> types` list and a `{ type: "section", id: "core-rules" }` entry explaining that it marks the start of a sheet section (ids: `core-rules`, `core-abilities`, `datasheet-characteristics`, `core-stratagems`), is never rendered, never splits columns or pages, and is what `generate --skip-*` uses to omit sections
- [X] T025 [P] Update `docs/CONTENT_AUTHORING.md`: in "Generating cheat sheets", add example commands for `--skip-core-stratagems` and a two-flag combination, plus one sentence on the `<lang>-no-<ids>[-print].pdf` output naming (full sheet never overwritten; a no-op skip keeps the standard name). In "Editions, revisions, and content", add a paragraph and YAML example for `{type: section, id: ...}` markers: the four ids, the first block must be a marker, one marker per id, placement before a section's own `page_break`/`column_reset`, and omit the marker for a section an edition lacks. Link `specs/015-skip-sheet-sections/contracts/section-marker-block.md` and `.../cli-skip-flags.md` (FR-015)
- [X] T026 [P] In `tests/integration/test_package_command.py`, add a test that runs `package_all(config, paths, tmp_path / "dist")` against a tmp copy of the project (same copy helper as the file's existing tests), asserts no returned path's name contains `-no-`, and for each staged `<edition>-<lang>.pdf` reads `out/<edition>/<latest revision>/<lang>.html` (`package_all` returns only the staged `list[Path]`, not documents) and asserts it contains every section signature from the reference table that the edition has - all four for `11e/en` and `11e/de`; `core-rules`, `core-abilities`, `core-stratagems` for `10e/de` (FR-014, C7)
- [X] T027 Run `uv run poe check` and confirm every gate passes: `ruff format --check`, `ruff check` + `pylint`, `bandit`, `ty check`, and the full `pytest` suite, including the docstring gate for `src/wh40k_cheatsheet/content/sections.py`
- [X] T028 Walk through `specs/015-skip-sheet-sections/quickstart.md` scenarios 2–10 end to end, using the T001 baseline for §2's byte-identity diff, and confirm every expected outcome

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies. T001 must run before any code or content change.
- **Foundational (Phase 2)**: Depends on Setup. BLOCKS all user stories. T006 is the root: T007 and
  T008 import it. T009 needs T006–T008. T010–T012 can be done in any order once T009 exists.
- **User Story 1 (Phase 3)**: Depends on Foundational. T015 → T016 → T017.
- **User Story 2 (Phase 4)**: Depends on US1 (T020 restructures T016's `_generate_one()`; T018/T019
  extend US1's test files).
- **User Story 3 (Phase 5)**: Depends on US2 (T023 verifies T020's two-pass pipeline; T021 extends
  the same test file as T013/T018).
- **Polish (Phase 6)**: T024–T026 can start any time after Foundational. T027/T028 depend on all
  stories.

### User Story Dependencies

- **US1 (P1)**: Needs only Foundational. Independently shippable MVP.
- **US2 (P2)**: Builds on US1's pipeline and CLI wiring. It is still independently *testable* via
  its own scenarios, but its implementation (T020) edits code US1 introduced.
- **US3 (P3)**: Mostly verification of behavior US1/US2 already deliver; its only code task (T023)
  is conditional.

### Within Each Phase

- Tests are written first and must fail before their implementation task.
- Same-file tasks run sequentially in ID order: `tests/unit/test_sections.py` (T002 → T003),
  `tests/integration/test_skip_sections_pdf.py` (T013 → T018 → T021),
  `tests/integration/test_skip_sections_cli.py` (T014 → T019),
  `src/wh40k_cheatsheet/pipeline.py` (T015 → T016 → T020 → T023).

### Parallel Opportunities

- **Foundational tests**: T002, T004, T005 (three different files).
- **Content markers**: T010, T011, T012 (three different content files).
- **US1 tests**: T013 and T014 (different files).
- **US2 tests**: T018 and T019 (different files).
- **US3 tests**: T021 and T022 (different files).
- **Polish**: T024, T025, T026 (different files), alongside any story once Foundational is done.

---

## Parallel Example: Foundational

```bash
# Tests, all different files:
Task: "Unit tests for section ids / marker validation in tests/unit/test_sections.py"            # T002
Task: "section markers are transparent to group_by_breaks in tests/unit/test_page_breaks.py"      # T004
Task: "resolve_content marker validation in tests/unit/test_content_resolver_sections.py"          # T005

# Content markers, all different files (after T009 exists):
Task: "Add section markers to editions/11e/2026-06-01-00/en/content.yaml"                           # T010
Task: "Add section markers to editions/11e/2026-06-01-00/de/content.yaml"                           # T011
Task: "Add section markers to editions/10e/2026-06-16-00/de/content.yaml"                           # T012
```

## Parallel Example: User Story 1

```bash
Task: "Per-flag PDF/HTML tests in tests/integration/test_skip_sections_pdf.py"                    # T013
Task: "CLI flag, help, and unknown-flag tests in tests/integration/test_skip_sections_cli.py"      # T014
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: capture the baseline (T001).
2. Phase 2: section module, transparent markers, validation, shipped markers (T002–T012). Confirm the
   existing suite is still green and output is unchanged.
3. Phase 3: pipeline and CLI for a single skip (T013–T017).
4. **STOP and VALIDATE**: quickstart.md §2 and §3.
5. Demoable: any one section can be dropped from a printout.

### Incremental Delivery

1. Setup + Foundational → markers in place, zero behavior change.
2. US1 → single-section skip (MVP) → validate.
3. US2 → multi-section skip + fail-before-write → validate (quickstart §4, §5).
4. US3 → print-friendly/multi-language/no-op consistency → validate (quickstart §6, §7).
5. Polish → docs, release-path regression test, full gate, full quickstart.

---

## Notes

- [P] = different files, no dependency on an incomplete task.
- [Story] labels map tasks to spec.md user stories for traceability.
- `content/sections.py` must stay free of imports from `content/resolver.py` and `pipeline.py`;
  callers convert its returned problems into `ContentError`/`PipelineError`. This is why F4's
  `ContentError` is raised in `pipeline.py` rather than inside `omit_sections()` as data-model.md §5
  sketches; the user-visible behavior (contract F4) is unchanged.
- No task changes `package_all()`; T026 only locks in that releases stay full (FR-014).
- Commit after each task or logical group; stop at any checkpoint to validate a story independently.
