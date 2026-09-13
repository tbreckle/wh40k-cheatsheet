---

description: "Task list for Alphabetical Core Abilities Glossary implementation"
---

# Tasks: Alphabetical Core Abilities Glossary

**Input**: Design documents from `/specs/013-glossary-alphabetical-sort/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/glossary-term-ordering.md, quickstart.md

**Tests**: Test tasks ARE included — the spec defines acceptance scenarios and success criteria, and
the constitution's Testing Standards (NON-NEGOTIABLE) require every new feature to ship with tests
covering its expected behavior and at least one boundary case.

**Organization**: Grouped by user story so each is an independently testable increment. Both stories
are verified against the same mechanism (Phase 1 + Phase 2); they differ in what they assert.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1, US2

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: The pure ordering function — the only new logic this feature introduces.

- [X] T001 Create `src/wh40k_cheatsheet/render/glossary.py` with a module docstring, a private `_sort_key(term: Any) -> str` implementing the fold `casefold()` → `unicodedata.normalize("NFD", …)` → drop chars where `unicodedata.combining(c)` is truthy (returning `""` for a missing or non-`str` term, per data-model.md §1), and a public `sort_glossary_terms(terms: list[Any]) -> list[Any]` returning `sorted(terms, key=lambda e: _sort_key(e.get("term") if isinstance(e, dict) else None))` — a new list, never mutating the input (data-model.md §2/§3). Google-style docstrings with `Args:`/`Returns:` on both, full type annotations, per the `008` docstring gate

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Wire the function into the render path so every glossary block is ordered.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 In `_environment()` in `src/wh40k_cheatsheet/render/html_renderer.py`, register the new function as a Jinja global: `env.globals["sort_glossary_terms"] = sort_glossary_terms  # ty: ignore[invalid-assignment]`, immediately after the existing `group_by_breaks` registration and covered by the same explanatory comment already there; add the import from `wh40k_cheatsheet.render.glossary` (depends on T001)
- [X] T003 [P] Re-export `sort_glossary_terms` from `src/wh40k_cheatsheet/render/__init__.py` — add it to the import line and to `__all__`, alongside `RenderError` and `render_html` (depends on T001)
- [X] T004 In the `glossary` branch of `templates/cheatsheet.html.j2`, change the term loop to `{%- for g in sort_glossary_terms(block['terms'] | default([])) -%}`, leaving the `<p class="term">` markup, the `term__name` span, and the `| safe` html handling exactly as they are (contracts G1/G9; depends on T002)
- [X] T005 In the header doc comment of `templates/cheatsheet.html.j2`, note on the `glossary` block entry that `terms` render alphabetically by `term` regardless of authored order, with accented characters sorting under their base letter (data-model.md §2)

**Checkpoint**: Every glossary block renders alphabetically; ready for story-level verification.

---

## Phase 3: User Story 1 - Look up a core ability during a game (Priority: P1) 🎯 MVP

**Goal**: The Core Abilities glossary in every generated cheat sheet reads A to Z, in the
alphabetical convention of its own language, with every authored entry preserved exactly.

**Independent Test**: Generate any edition/language and read the glossary top to bottom — every
entry is ordered relative to the one before it, `ÜBERSCHWERER LÄUFER` sits between `TÖDLICHE
TREFFER` and `VERHEERENDE WUNDEN` in German, and the entry count and definition texts match the
content file exactly.

### Tests for User Story 1 ⚠️

- [X] T006 [US1] Unit tests for ordering correctness in `tests/unit/test_glossary_order.py`: a shuffled ASCII term list sorts alphabetically (FR-001/G1); `Ä`/`Ö`/`Ü` sort under `A`/`O`/`U` and `ß` under `ss`, asserted with the real German case `["ZUSÄTZLICHE ATTACKEN", "ÜBERSCHWERER LÄUFER", "TÖDLICHE TREFFER", "VERHEERENDE WUNDEN"]` ordering as `TÖDLICHE TREFFER` → `ÜBERSCHWERER LÄUFER` → `VERHEERENDE WUNDEN` → `ZUSÄTZLICHE ATTACKEN` (FR-003/G3); mixed-case entries interleave rather than forming separate runs (FR-004/G4); ordering ignores `text`/`html` entirely (FR-002/G2)
- [X] T007 [US1] Unit tests for stability and entry preservation in `tests/unit/test_glossary_order.py`: two entries with the identical `term` keep their authored relative order (FR-005/G5); output length equals input length and every entry object is present with its `text`/`html` unchanged (FR-006/G6); the input list is not mutated and the returned list is a distinct object (data-model.md §3) — depends on T006 (same file)
- [X] T008 [US1] Unit tests for boundary and malformed input in `tests/unit/test_glossary_order.py`: an empty `terms` list returns empty, a single-entry list returns that entry, an entry whose `term` key is missing or is a non-string sorts first without raising (G10/G11) — depends on T007 (same file)
- [X] T009 [US1] Integration test in `tests/integration/test_glossary_order_cross_language.py`: for every real (edition, language) that declares a glossary — `11e`/`en`, `11e`/`de`, `10e`/`de` — render via `render_html` and extract the rendered `term__name` values; assert every adjacent pair is correctly ordered by the same fold, and that the rendered term count and definition texts exactly match the authored `content.yaml` (FR-001/FR-006; SC-001/SC-002/SC-004; contracts G1/G3/G6)
- [X] T010 [US1] Integration test in `tests/integration/test_glossary_order_cross_language.py`: the rendered `11e`/`en` glossary term sequence is identical to the authored sequence, proving the feature is a no-op for already-alphabetical content (SC-005; contracts G6) — depends on T009 (same file)
- [X] T011 [US1] Integration test in `tests/integration/test_glossary_order_cross_language.py`: rendering the same content with `document.print_friendly` set to `True` produces the identical glossary term sequence as the standard render, confirming the ordering reaches every output variant (FR-008; contracts G8) — depends on T010 (same file)

**Checkpoint**: MVP — every shipped cheat sheet's glossary is alphabetical in its own language, with
no entry lost or altered, and English output is provably unchanged.

---

## Phase 4: User Story 2 - Author or translate glossary entries without policing order (Priority: P2)

**Goal**: Authors and translators can append or reorder entries wherever convenient in the content
file; the generated sheet comes out identical either way.

**Independent Test**: Append a term at the end of a content file's glossary block, regenerate, and
confirm it lands in its alphabetical position — then reverse the whole authored list, regenerate,
and confirm the output is unchanged.

### Tests for User Story 2 ⚠️

- [X] T012 [US2] Unit test in `tests/unit/test_glossary_order.py`: taking the real German 11e term sequence, sorting the reversed and an arbitrarily shuffled permutation both yield the identical result — authored order has no effect on output (FR-007; contracts G7); and an entry appended at the end of an already-sorted list lands in its alphabetical position, not last (User Story 2 scenario 1) — depends on T008 (same file)
- [X] T013 [US2] Integration test in `tests/integration/test_glossary_order_cross_language.py`: rendering a document whose glossary `terms` list is reversed produces a glossary region byte-identical to rendering the same content unreversed (FR-007; contracts G7) — depends on T011 (same file)

**Checkpoint**: Both stories independently verified; content authoring is free of manual ordering.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and end-to-end validation.

- [X] T014 [P] Update the glossary section of `docs/CONTENT_AUTHORING.md` (the `{type: glossary}` / `spanning` passage) to state that term order is produced at generation time — authors need not maintain alphabetical order by hand, accented characters sort under their base letter, and duplicate terms keep authored order — with a pointer to `specs/013-glossary-alphabetical-sort/contracts/glossary-term-ordering.md` (FR-010)
- [X] T015 Run `uv run poe check` and confirm every gate passes: `ruff format --check`, `ruff check` + `pylint`, `bandit`, `ty check`, and the full `pytest` suite — including the pre-existing `tests/integration/test_reproducible.py`, whose byte-identical guarantee would break on an unstable sort (SC-003)
- [X] T016 Run every scenario in `quickstart.md` end-to-end (generate both editions, verify the German ordering and the `ÜBERSCHWERER LÄUFER` placement, confirm the English output diffs clean against the pre-feature commit, confirm reordered authored content produces identical output, and visually confirm the spanning full-width glossary layout and print-friendly variant are unchanged) and confirm expected outcomes

---

## Phase 6: Amendment (2026-09-13) — Leading-Bracket Weapon-Ability Terms

**Purpose**: Real weapon-ability terms (`10e` German glossary: `[ANTI-X Y+] (24.03)`, `[PISTOL]
(24.27)`, …) are authored with a leading `[`, which folded before every lowercase letter under the
original `_sort_key`, clustering every such term ahead of the entire rest of the glossary regardless
of its actual first letter. See spec.md's 2026-09-13 amendment (FR-011/SC-007) and
`contracts/glossary-term-ordering.md` G12.

**Goal**: A term whose first character is `[` sorts under its first real letter, interleaved
correctly with unbracketed terms; a `[` anywhere else in a term is unaffected; every other
guarantee (G1–G11) continues to hold unchanged.

- [X] T017 In `_sort_key` in `src/wh40k_cheatsheet/render/glossary.py`, strip a single leading `[` from `term` (if present) before the existing `casefold()`/NFD fold — `term = term.removeprefix("[")` — and update its docstring (data-model.md §2 step 0; contracts G12)
- [X] T018 [P] Unit tests in `tests/unit/test_glossary_order.py`: a term with a leading `[` sorts under its first real letter among unbracketed terms; leading-bracket terms interleave correctly with unbracketed ones (not clustered together); a `[` appearing anywhere other than the first character is left untouched (FR-011; contracts G12)
- [X] T019 [P] Update `contracts/glossary-term-ordering.md` (new guarantee G12, amendment note, mechanism text), `data-model.md` (§2 step 0, new worked example), `research.md` (new §5), `quickstart.md` (new validation scenario), and `docs/CONTENT_AUTHORING.md`'s glossary-ordering passage for the leading-bracket rule

**Checkpoint**: `poe check` green; a term like `[ANTI-X Y+] (24.03)` sorts under `A`, not ahead of
every other term.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — T001 is the only new logic.
- **Foundational (Phase 2)**: Depends on Setup (T002/T003 import the function from T001; T004 calls
  the global registered by T002) — BLOCKS both user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational. Test-only — Phases 1 + 2 already deliver the
  behavior; T006–T011 verify it against the P1 acceptance criteria.
- **User Story 2 (Phase 4)**: Depends on Foundational. Test-only, and independent of US1 — it
  asserts input-order irrelevance rather than output correctness, so it holds even if US1's
  assertions were removed.
- **Polish (Phase 5)**: T014 can start any time after Phase 2; T015/T016 depend on both stories.

### User Story Dependencies

- **US1 (P1)**: Depends only on Phase 1 + Phase 2. The MVP.
- **US2 (P2)**: Depends only on Phase 1 + Phase 2. Does **not** depend on US1 — the two stories share
  a mechanism but neither's tests rely on the other's.

### Within Each User Story

- Tests only — there is no implementation step to sequence tests before, since Setup + Foundational
  contain the entire mechanism. Within a story, tasks touching the same test file are sequential.

### Parallel Opportunities

- T003 is `[P]`: `render/__init__.py` is touched by no other task. T005 is deliberately **not**
  `[P]` — it edits a different region of `templates/cheatsheet.html.j2` than T004, but the same
  file, so sequence it after T004 to avoid a conflicting patch.
- T014 is `[P]` against everything in Phases 3–4: `docs/CONTENT_AUTHORING.md` is touched by no other
  task.
- **Test tasks are deliberately not marked `[P]`**: all six US1 tests land in just two files
  (`tests/unit/test_glossary_order.py`, `tests/integration/test_glossary_order_cross_language.py`),
  and US2's two extend those same files. They are split by concern for traceability, not for
  parallelism.
- Across stories: US1 (Phase 3) and US2 (Phase 4) can be worked by different people once Phase 2
  lands — but they share both test files, so coordinate or sequence the file edits.

---

## Parallel Example: Phase 2

```bash
# After T001 and T002 land, these touch different files with no ordering constraint:
Task: "Re-export sort_glossary_terms from src/wh40k_cheatsheet/render/__init__.py"     # T003
Task: "Document alphabetical term ordering in docs/CONTENT_AUTHORING.md"               # T014
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001) — the sort function.
2. Complete Phase 2: Foundational (T002–T005) — CRITICAL; this is the entire mechanism.
3. Complete Phase 3: User Story 1 (T006–T011).
4. **STOP and VALIDATE**: German glossaries read alphabetically, English output is unchanged, no
   entry lost or altered.
5. Ship if ready — the reader-facing value is fully delivered at this point.

### Incremental Delivery

1. Setup + Foundational → mechanism in place.
2. Add US1 → validate → ship (MVP: the glossary is alphabetical).
3. Add US2 → validate → ship (authoring order provably irrelevant).
4. Polish (T014–T016) → docs updated, gates green, quickstart walked end to end.

---

## Notes

- `[P]` tasks = different files, no dependencies on incomplete tasks.
- No `content.yaml` is modified by this feature — if a task tempts you to edit edition content,
  re-read research.md §3; rewriting content was explicitly rejected.
- The English 11e glossary is already alphabetical: T010 exists to keep that a proven no-op, so a
  regression there is a real failure, not an expected diff.
- Commit after each task or logical group; stop at any checkpoint to validate a story independently.
