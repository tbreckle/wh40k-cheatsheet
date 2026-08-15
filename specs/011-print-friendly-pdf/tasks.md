---

description: "Task list for Print-Friendly PDF Flag implementation"
---

# Tasks: Print-Friendly PDF Flag

**Input**: Design documents from `/specs/011-print-friendly-pdf/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/print-friendly-flag.md, quickstart.md

**Tests**: Test tasks ARE included — the spec defines acceptance scenarios and success criteria,
and the constitution's Testing Standards (NON-NEGOTIABLE) require every new feature to ship with
tests covering its expected behavior and at least one boundary case.

**Organization**: Grouped by user story so the story is an independently testable increment. This
feature has a single user story (P1) — the whole feature.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Extend the `GeneratedDocument` shape so the print-friendly output paths have somewhere
to live before anything writes to them.

- [X] T001 Add `print_html_path: Path | None = None` and `print_pdf_path: Path | None = None` fields to the `GeneratedDocument` dataclass in `src/wh40k_cheatsheet/pipeline.py`, with a docstring `Attributes:` entry for each (data-model.md §3)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The entire rendering mechanism (grayscale CSS + watermark omission), the pipeline's
second render/write pass, and the CLI flag — all required before the story can be verified.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 In `templates/cheatsheet.html.j2`, resolve every `:root` color custom property (`--green-dark`, `--green-sub`, `--green-line`, `--ink`, `--muted`, `--cream`, `--cream-brd`, `--info-bg`, `--info-brd`, `--your-bg`, `--your-ink`, `--opp-bg`, `--opp-ink`, `--either-bg`, `--either-ink`, `--rule`) via a server-side Jinja conditional on a new `print_friendly` template var, plus gate the two non-variable overrides (`.callout--info .callout__icon` color, `table.data tbody tr:nth-child(even) td` background) behind the same flag, with the grayscale values from data-model.md §2 / contracts/print-friendly-flag.md's CSS mechanism. **Deviation from original task text**: resolved at `:root` rather than a `body.print-friendly` class override — `@page` margin-box content (running header/footer) inherits custom properties from the page context, not `<body>`, so a body-scoped override would miss it (research.md §1 amendment)
- [X] T003 [P] In `templates/cheatsheet.html.j2`, add `class="{{ 'print-friendly' if print_friendly else '' }}"` to the `<body>` tag, and wrap the existing `<img class="page-watermark" ...>` tag in `{% if not print_friendly %}...{% endif %}` so it is omitted entirely (not merely hidden) when print-friendly (contracts G2/G5; research.md §2)
- [X] T004 [P] Update the header doc comment in `templates/cheatsheet.html.j2` to document the new `document.print_friendly` (bool, default `false`) context key, its effect (grayscale palette + watermark omission), and that it is pipeline-set, not an authored `content.yaml` field (data-model.md §1)
- [X] T005 Add a `print_friendly: bool = False` keyword-only parameter to `generate()` in `src/wh40k_cheatsheet/pipeline.py`, threaded through to each `_generate_one()` call, with an updated `Args:` docstring entry (contracts C1/C2; depends on T001)
- [X] T006 In `_generate_one()` in `src/wh40k_cheatsheet/pipeline.py`: accept the new `print_friendly` parameter; after writing the standard HTML/PDF as today, when `print_friendly` is `True`, render a second HTML from `{**context, "document": {**context["document"], "print_friendly": True}}`, write it to `{out_dir}/{language}-print.html`, convert it to `{out_dir}/{language}-print.pdf` via `render_pdf`, and return a `GeneratedDocument` with `print_html_path`/`print_pdf_path` populated (`None` when the flag is unset) — add `Raises:`/`Args:` docstring updates per the `008` docstring gate (depends on T001, T002, T003, T005; contracts O1/O2/O3)
- [X] T007 Add `--print-friendly` (`action="store_true"`, default `False`) to the `generate` subparser in `build_parser()` in `src/wh40k_cheatsheet/cli.py`, with a `help=` string (contracts C1)
- [X] T008 In `_cmd_generate()` in `src/wh40k_cheatsheet/cli.py`, pass `print_friendly=args.print_friendly` through to `generate()`, and print an additional result line per document (`f"{doc.edition_id} / {doc.revision} / {doc.language} (print-friendly) -> {doc.print_pdf_path}"`) when `doc.print_pdf_path` is not `None` (depends on T006, T007; contracts C4)

**Checkpoint**: `generate --print-friendly` produces a second, grayscale, watermark-free PDF/HTML
pair alongside the standard pair; omitting the flag changes nothing.

---

## Phase 3: User Story 1 - Generate a printer-friendly PDF via a CLI flag (Priority: P1) 🎯 MVP

**Goal**: A user passes `--print-friendly` to `generate` and receives an additional PDF rendered
entirely in black/white/grey, with no background watermark, matching the standard PDF's text,
structure, and page breaks exactly — while the standard PDF is still produced as usual and nothing
changes when the flag is omitted.

**Independent Test**: Run `generate --edition 11e --language en --print-friendly` and inspect
`out/11e/<revision>/en-print.pdf`: no non-grayscale colors anywhere, no watermark on any page, same
text/page count as `en.pdf`, and the four callout/stratagem-timing variants remain visually
distinguishable from one another.

### Tests for User Story 1 ⚠️

- [X] T009 [P] [US1] Integration test: rendering real `11e` content with `print_friendly=True`, every element's computed `background_color`/`color`/`border-top-color` (via WeasyPrint's box-tree API, the same technique as `test_page_logo_pdf.py`) is grayscale (R == G == B), in `tests/integration/test_print_friendly_pdf.py` (contracts G1; FR-002; SC-001) — implemented against a synthetic all-variants document (covers every block/variant type in one render) rather than real content alone, plus a real-content watermark-absence check in T010; also added a sanity-check test confirming the same content *without* the flag still contains color, so the grayscale assertion isn't vacuously true
- [X] T010 [P] [US1] Integration test: rendering real `11e` content with `print_friendly=True`, no `<img>` box exists anywhere in the page tree, on every page, in `tests/integration/test_print_friendly_pdf.py` (contracts G2; FR-003; SC-002)
- [X] T011 [P] [US1] Integration test: the print-friendly rendering's extracted text content and page count exactly match the standard rendering's, for the same (edition, revision, language), in both `en` and `de`, in `tests/integration/test_print_friendly_pdf.py` (contracts G3; FR-004; SC-003) — implemented via exact-substring equality of the `<article class="cheatsheet">...</article>` region (verified empirically byte-identical) plus a `weasyprint` page-count comparison
- [X] T012 [P] [US1] Integration test: the three stratagem-timing variants (`--your-bg`, `--opp-bg`, `--either-bg`) and the two callout variants (`--cream`, `--info-bg`) each resolve to a distinct grey value (not collapsed to one identical shade) in the print-friendly rendering, in `tests/integration/test_print_friendly_pdf.py` (contracts G4; FR-005; SC-005)
- [X] T013 [US1] CLI-level integration test: `main(["generate", "--edition", "11e", "--language", "en", "--print-friendly"])` writes both `en.pdf`/`en.html` and `en-print.pdf`/`en-print.html`, and stdout contains one result line for each, in `tests/integration/test_print_friendly_pdf.py` (contracts C1–C4, O1–O3; depends on T006–T008)
- [X] T014 [US1] Regression test: `main(["generate", "--edition", "11e", "--language", "en"])` (flag omitted) writes only `en.pdf`/`en.html` — no `en-print.*` files exist afterward, and stdout contains exactly the pre-feature single result line — in `tests/integration/test_print_friendly_pdf.py` (contracts C3; FR-008; SC-004)

**Implementation-time bug found and fixed by these tests**: T009 initially failed on the table's
zebra-stripe cells — the print-friendly override for `table.data tbody tr:nth-child(even) td` was
placed *before* the base rule of equal specificity in the stylesheet, so the base rule (later in
source order) won the cascade and the original tinted color still rendered. Fixed by moving both
non-variable print-friendly overrides to the end of the `<style>` block, after every rule they
override (T002 amended accordingly; templates/cheatsheet.html.j2).

### Implementation for User Story 1

- No story-specific implementation — Phase 1 + Phase 2 (T001–T008) already deliver this behavior;
  T009–T014 verify it against the P1 acceptance criteria.

**Checkpoint**: MVP — `--print-friendly` reliably produces a correct grayscale, watermark-free,
content-identical PDF alongside the standard one, and omitting it changes nothing.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation and documentation.

- [X] T015 Run every scenario in `quickstart.md` end-to-end (both files produced, flag-omitted path unaffected, visual grayscale/no-watermark/content-parity check, automated test suite) and confirm expected outcomes
- [X] T016 [P] Add a "Print-friendly output" section to `README.md` (near the existing "Page logo watermark" section), documenting the `--print-friendly` flag, its `{language}-print.pdf`/`.html` output naming, and a link to `specs/011-print-friendly-pdf/contracts/print-friendly-flag.md`; also add a `--print-friendly` example to the existing `generate` usage examples near the top of the CLI section

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Depends on Setup (T006 needs the `GeneratedDocument` fields from
  T001) — BLOCKS the user story. Contains the entire rendering + pipeline + CLI mechanism.
- **User Story 1 (Phase 3)**: Depends on Foundational. The only story — also the MVP.
- **Polish (Phase 4)**: Depends on the story being complete.

### User Story Dependencies

- **US1 (P1)**: Depends only on Phase 1 + Phase 2 — the only user story in this feature.

### Within the User Story

- Tests only — there is no implementation step to sequence tests before, since Setup + Foundational
  already deliver the mechanism. T013 depends on T006–T008 (the CLI/pipeline wiring it exercises).

### Parallel Opportunities

- **Foundational**: T003 and T004 are independent of T002 and each other (same file, different
  regions/purpose).
- **US1**: T009, T010, T011, T012 are all parallel to each other (same file, distinct independent
  cases); T013 and T014 depend on Foundational being complete but are independent of each other and
  of T009–T012.
- **Polish**: T016 has no dependency on T015.

---

## Parallel Example: User Story 1 tests

```bash
# Independent test cases within the same new file:
Task: "Grayscale-only computed-style test in tests/integration/test_print_friendly_pdf.py"
Task: "Watermark-box-absent test in tests/integration/test_print_friendly_pdf.py"
Task: "Content/page-count parity test in tests/integration/test_print_friendly_pdf.py"
Task: "Distinct-grey-shades-per-variant test in tests/integration/test_print_friendly_pdf.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001).
2. Complete Phase 2: Foundational (T002–T008) — CRITICAL; this is the entire mechanism.
3. Complete Phase 3: User Story 1 (T009–T014).
4. **STOP and VALIDATE**: `generate --print-friendly` against real `11e` content produces a correct
   grayscale, watermark-free PDF alongside the unaffected standard PDF, in both languages.
5. Demonstrable MVP — an opt-in printer-friendly output, verified not to break anything else.

### Incremental Delivery

1. Setup + Foundational → the mechanism (template, pipeline, CLI) all exist.
2. US1 → grayscale, watermark-absence, content-parity, distinguishability, CLI wiring, and
   flag-omitted regression all verified (MVP!) → validate → demo.
3. Polish → quickstart validation + docs.

---

## Notes

- [P] = different files or independent regions of the same file, no dependencies. Tasks sharing a
  file are grouped but remain logically independent.
- [Story] label maps each task to its user story for traceability.
- Because this feature's entire implementation lives in Setup + Foundational, the story's
  "Implementation" subsection intentionally contains no new tasks — only its Tests subsection does
  (same shape as feature 010's Phase 3).
- Tests (T009–T014) must fail before Foundational (T002–T008) is complete, and pass once it is.
- Commit after each task or logical group; stop at any checkpoint to validate independently.
