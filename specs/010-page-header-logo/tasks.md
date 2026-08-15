---

description: "Task list for Page Header Logo implementation"
---

# Tasks: Page Header Logo

**Input**: Design documents from `/specs/010-page-header-logo/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/page-logo.md, quickstart.md

**Tests**: Test tasks ARE included — the spec defines validation scenarios and the constitution's
Testing Standards are non-negotiable.

**Organization**: Grouped by user story so the story is an independently testable increment.

> **Not template-only, unlike `007`/`009`**: Research found WeasyPrint does NOT fail loudly on a
> missing referenced image (research.md §4) — it silently logs and continues. FR-005 therefore
> requires a small, explicit pre-flight check in `pipeline.py`, in addition to the
> `templates/cheatsheet.html.j2` CSS/markup change.
>
> **2026-08-14 amendment (Phases 5–8 below)**: the top-right corner logo built in Phases 1–4 was
> replaced with a full-page, 45°-rotated, 30%-opacity background watermark, per a follow-up
> `/speckit-clarify` request. Phases 1–4 remain below as an accurate historical record — T001/T002
> (`Paths.images_root` + the pre-flight check) are still valid and unchanged; T003/T004/T006–T011
> describe the superseded corner-logo mechanism, replaced by Phases 5–8.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: A `Paths.images_root` field so the pipeline knows where to find `logo_40k.png` for the
pre-flight check (Phase 2).

- [X] T001 Add an `images_root: Path` field to the `Paths` dataclass in `src/wh40k_cheatsheet/pipeline.py`, alongside the existing `editions_root`/`templates_root`/`out_root` fields (data-model.md Paths entity)
- [X] T002 Populate `images_root=project_root / "images"` in `_default_paths` in `src/wh40k_cheatsheet/cli.py`, matching the existing construction pattern for the other three roots (depends on T001)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The rendering mechanism (template/CSS) and the fail-loud guarantee (pre-flight check) —
both required before the story can be verified.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 In `templates/cheatsheet.html.j2`: enlarge the `@page` top margin from `7mm` to `15mm`; add the CSS rule `.page-logo { position: fixed; top: -14.7mm; right: 6mm; height: 50px; width: auto; }`; add one `<img class="page-logo" src="../images/logo_40k.png" alt="">` in the document body (contracts/page-logo.md CSS mechanism; research.md §2/§2b — negative offset required since `position: fixed`'s containing block is the content box, not the page edge)
- [X] T004 [P] Update the header doc comment in `templates/cheatsheet.html.j2` to document the logo as a fixed, unconditional page element (not an authored content-block flag)
- [X] T005 Add a pre-flight existence check in `_generate_one` (or `generate`) in `src/wh40k_cheatsheet/pipeline.py`: verify `(paths.images_root / "logo_40k.png").is_file()` before rendering; raise `PdfError` naming the expected path if it fails (depends on T001; research.md §4; contracts/page-logo.md F1; FR-005) — add a `Raises:` line to the function's docstring per the `008` docstring gate

**Checkpoint**: The logo renders correctly on a real page, and a missing asset now fails the pipeline
instead of silently continuing.

---

## Phase 3: User Story 1 - See consistent branding on every page (Priority: P1) 🎯 MVP

**Goal**: Every page of every generated document shows the logo, top-right, at a consistent 50px
height with its source aspect ratio preserved, never overlapping any existing content.

**Independent Test**: Generate the real `11e` content and inspect every page: each one shows the
logo in the top-right corner, same size, undistorted, not overlapping any other content.

### Tests for User Story 1 ⚠️

- [X] T006 [P] [US1] Integration test: the logo's rendered box height is 50px and its width matches the source image's aspect ratio (2184:668), on every page, in `tests/integration/test_page_logo_pdf.py`, using the box-inspection methodology from research.md §2 (FR-001/FR-002; SC-001/SC-002/SC-003)
- [X] T007 [P] [US1] Integration test: rendering the real `11e` content in both `en` and `de`, the logo's box never overlaps any other rendered box's position on any page, in `tests/integration/test_page_logo_pdf.py` (FR-004; SC-004; research.md §2b's verified zero-overlap methodology)
- [X] T008 [P] [US1] Regression test: regenerating the real `11e` content produces the same page count in both languages as before this feature, in `tests/integration/test_page_logo_pdf.py` (SC-005)
- [X] T009 [US1] Integration test: with `images/logo_40k.png` temporarily missing, `generate` fails with a non-zero exit and a message naming the expected logo path, and writes no output, in `tests/integration/test_page_logo_pdf.py` (depends on T005; FR-005; contracts/page-logo.md F1)

### Implementation for User Story 1

- No story-specific implementation — Phase 1 + Phase 2 (T001–T005) already deliver this behavior;
  T006–T009 verify it against the P1 acceptance criteria.

**Checkpoint**: MVP — the logo reliably renders correctly on every page, and a missing asset reliably
fails generation instead of shipping a broken PDF.

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation and documentation.

- [X] T010 Run every scenario in `quickstart.md` end-to-end (logo on every page, no overlap, existing content unaffected, missing-asset failure) and confirm expected outcomes
- [X] T011 [P] Document the logo behavior in `README.md` — that it is unconditional (not an authored flag), its fixed 50px size, and a link to `specs/010-page-header-logo/contracts/page-logo.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately. T002 depends on T001 (same new field).
- **Foundational (Phase 2)**: Depends on Setup (T005's check needs `images_root` from T001) — BLOCKS
  the user story.
- **User Story 1 (Phase 3)**: Depends on Foundational. The only story — also the MVP.
- **Polish (Phase 4)**: Depends on the story being complete.

### User Story Dependencies

- **US1 (P1)**: Depends only on Phase 1 + Phase 2 — the only user story in this feature.

### Within the User Story

- Tests only — there is no implementation step to sequence tests before, since Setup + Foundational
  already deliver the mechanism. T009 depends on T005 (the check it's testing must exist).

### Parallel Opportunities

- **Foundational**: T004 (doc comment) is independent of T003 (CSS/markup) and T005 (Python check),
  though T003/T004 touch the same file (different regions).
- **US1**: T006, T007, T008 are all parallel to each other (same file, distinct independent cases);
  T009 depends on T005 but is independent of T006–T008.
- **Polish**: T011 parallel to T010.

---

## Parallel Example: User Story 1 tests

```bash
# Different, independent test cases within the same file:
Task: "Size/aspect-ratio box-width test in tests/integration/test_page_logo_pdf.py"
Task: "No-overlap test across real content and both languages in tests/integration/test_page_logo_pdf.py"
Task: "Page-count regression test in tests/integration/test_page_logo_pdf.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T002).
2. Complete Phase 2: Foundational (T003–T005) — CRITICAL; this is the entire mechanism plus the
   fail-loud guarantee.
3. Complete Phase 3: User Story 1 (T006–T009).
4. **STOP and VALIDATE**: the real `11e` content renders with the logo on every page, no overlap, in
   both languages; removing the logo file fails generation clearly.
5. Demonstrable MVP — consistent branding, verified not to break anything else.

### Incremental Delivery

1. Setup + Foundational → the mechanism and the fail-loud guarantee both exist.
2. US1 → presence, size, aspect ratio, no-overlap, regression-safety, and fail-loud behavior all
   verified (MVP!) → validate → demo.
3. Polish → quickstart validation (incl. real `11e` content regression check) + docs.

---

## Notes

- [P] = different files, no dependencies. Tasks sharing a file are grouped but remain logically
  independent.
- [Story] label maps each task to its user story for traceability.
- Because this feature's entire implementation lives in Setup + Foundational, the story's
  "Implementation" subsection intentionally contains no new tasks — only its Tests subsection does.
- Tests (T006–T009) must fail before Foundational (T003–T005) is complete, and pass once it is.
- Commit after each task or logical group; stop at any checkpoint to validate independently.

---

## Phase 5: Amendment Setup (2026-08-14) — Revert the corner-logo margin

**Purpose**: Undo the margin enlargement the corner logo needed; the background watermark doesn't
live in the margin band.

- [X] T012 Revert the `@page` top margin in `templates/cheatsheet.html.j2` from `15mm` back to `7mm` (i.e. `margin: 7mm 6mm 8mm 6mm`) (research.md §3)

---

## Phase 6: Amendment Foundational (2026-08-14) — The watermark rendering mechanism

**Purpose**: Replace the corner-logo CSS/markup with the background-watermark CSS/markup.

**⚠️ CRITICAL**: No amendment user-story work can begin until this phase is complete.

- [X] T013 Replace the `.page-logo` CSS rule with `.page-watermark` in `templates/cheatsheet.html.j2`: `position: fixed; left: -14.71mm; top: 106.72mm; width: 227.42mm; height: 69.56mm; transform: rotate(45deg); opacity: 0.3;` — deliberately no `z-index` (research.md §4 — a negative value was tested and found to hide the watermark entirely; DOM order alone puts it behind subsequent content) (contracts/page-logo.md CSS mechanism)
- [X] T014 [P] Update the `<img>` tag's class from `page-logo` to `page-watermark` in `templates/cheatsheet.html.j2` (same position in the document — immediately after `<body>`, before `<article class="cheatsheet">` — so DOM order keeps it painting behind)
- [X] T015 [P] Update the header doc comment in `templates/cheatsheet.html.j2` to describe the watermark (full-page, 45°-rotated, 30% opacity, behind content) instead of the corner logo

**Checkpoint**: The watermark renders correctly on a real page — faint, diagonal, behind content.

---

## Phase 7: Amendment User Story 1 (2026-08-14) - See a faint, consistent brand watermark on every page (Priority: P1) 🎯 MVP

**Goal**: Every page of every generated document shows the logo as a large, 45°-rotated,
≈30%-opacity watermark behind the content, fully visible with no cropping, never obscuring
anything.

**Independent Test**: Generate the real `11e` content and inspect every page: each one shows a
faint, diagonal watermark behind all text, at the same position/size/rotation/opacity, with
everything else still fully readable.

### Tests for Amendment User Story 1 ⚠️

- [X] T016 [US1] Rewrite the presence/size test in `tests/integration/test_page_logo_pdf.py`: assert the watermark's (pre-transform) box width/height match the computed 227.42mm×69.56mm (859.56×262.91px, within tolerance) on every page, its `transform` style includes a 45° (`π/4` rad) rotation, and its `opacity` style is ≈0.3 (FR-002/FR-003/FR-004; SC-002/SC-003)
- [X] T017 [P] [US1] Keep/adapt the position-consistency test (`test_logo_same_position_on_every_page_both_languages`) in `tests/integration/test_page_logo_pdf.py` — same underlying logic, now asserting on the watermark's new position, across every page in both `en` and `de` (FR-006)
- [X] T018 [P] [US1] Replace the old overlap-avoidance test with a stacking-order test in `tests/integration/test_page_logo_pdf.py`: assert the `<img class="page-watermark">` appears before `<article class="cheatsheet">` in the rendered HTML's DOM order (the structural proxy for "paints behind," since no `z-index` is set) — the old "zero geometric overlap" check no longer applies, since the watermark is now deliberately large and positioned behind content, not around it (FR-005; SC-004; research.md §4)
- [X] T019 [P] [US1] Keep the page-count regression test (`test_regenerating_real_content_keeps_same_page_count`) in `tests/integration/test_page_logo_pdf.py` unchanged — still asserts 3 pages `en` / 4 pages `de` (SC-005)
- [X] T020 [US1] Re-run the two existing missing-asset fail-loud tests (`test_missing_logo_asset_fails_generation_via_cli`, `test_missing_logo_asset_raises_pdf_error_directly`) in `tests/integration/test_page_logo_pdf.py` unmodified and confirm they still pass — the underlying pipeline check is untouched by this amendment (FR-007; contracts/page-logo.md F1)

### Implementation for Amendment User Story 1

- No story-specific implementation — Phase 5 + Phase 6 (T012–T015) already deliver this behavior;
  T016–T020 verify it against the P1 acceptance criteria.

**Checkpoint**: MVP — the watermark reliably renders correctly on every page, stays behind all
content, and the existing fail-loud guarantee for a missing asset still holds.

---

## Phase 8: Amendment Polish (2026-08-14)

**Purpose**: End-to-end validation and documentation for the amendment.

- [X] T021 Run every scenario in `quickstart.md` end-to-end (watermark on every page, readability over dense content, cross-page/language consistency, existing-content regression, missing-asset failure) and confirm expected outcomes
- [X] T022 [P] Update the "Page logo" section of `README.md` to describe the background watermark (45°, 30% opacity, full-page) instead of the top-right corner logo, keeping the link to `specs/010-page-header-logo/contracts/page-logo.md`

---

## Amendment Dependencies & Execution Order

- **Phase 5**: No dependencies — start immediately.
- **Phase 6**: Depends on Phase 5 — BLOCKS Phase 7. Contains the entire rendering mechanism
  (T013–T015).
- **Phase 7**: Depends on Phase 6. The only story — also the MVP for this amendment.
- **Phase 8**: Depends on Phase 7 being complete.
- **Parallel**: T014/T015 independent of T013 and each other (same file, different regions); T017,
  T018, T019 all parallel to each other and to T016 (same file, distinct independent cases); T020
  is independent of all of them; T022 parallel to T021.
- T016–T019 must fail against the pre-amendment (corner-logo) code before Phase 6 lands, and pass
  once it does; T020 must continue passing throughout (it was never broken by this amendment).

---

## Phase 9: Opacity Tuning (2026-08-15)

**Purpose**: Direct follow-up request — "change the opacity of the image to alpha of 0.05" — turns
the watermark fainter still than the originally-clarified 0.3 (the user had already hand-tuned it to
an intermediate 0.1 before this request landed).

- [X] T023 Change `.page-watermark`'s `opacity` from `0.1` to `0.05` in `templates/cheatsheet.html.j2`, and update the header doc comment's "faint (X% opacity)" wording to match
- [X] T024 [P] Update `EXPECTED_OPACITY` in `tests/integration/test_page_logo_pdf.py` from `0.3` to `0.05`
- [X] T025 [P] Update the "Page logo watermark" section of `README.md` from "30% opacity" to "5% opacity"
- [X] T026 [P] Update spec.md/plan.md/research.md/data-model.md/contracts/page-logo.md/quickstart.md opacity references (30%/0.3 → 5%/0.05) for consistency with the shipped value; Phases 1–8 task descriptions above are left as an accurate historical record of what those tasks changed at the time, not updated retroactively

**Checkpoint**: Rendered watermark opacity is 0.05 everywhere it's asserted or documented.
