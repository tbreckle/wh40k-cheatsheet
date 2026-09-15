---

description: "Task list for GitFlow CI/CD Release Pipeline implementation"
---

# Tasks: GitFlow CI/CD Release Pipeline

**Input**: Design documents from `/specs/012-gitflow-release-pipeline/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/*.md, quickstart.md

**Tests**: Test tasks ARE included — the constitution's Testing Standards (NON-NEGOTIABLE) require
every new feature to ship with tests, and the new `versioning`/`package` Python surface is fully
unit/integration-testable. The GitHub Actions workflow YAML itself is **not** pytest-testable (per
plan.md's Testing section); its verification tasks are explicit manual quickstart walkthroughs
against a real GitHub remote instead of automated tests.

**Organization**: Grouped by user story (US1 publish-on-merge, US2 build-everywhere, US3
downloadable pre-release artifacts), in spec.md's priority order.

> **Single shared workflow file**: unlike most features, all three stories extend the *same*
> `.github/workflows/quality.yml` file incrementally — Foundational adds the generic `build` job,
> US1 adds its artifact-upload condition and the `publish-release` job, US3 further broadens that
> same upload condition and adds the `validate-version` job/gating. This layered-extension shape is
> unavoidable given it's one workflow file; each story's tasks below say exactly which prior task's
> output they extend.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1, US2, US3

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: This repository is not yet a git repository — GitFlow branches must exist locally
before any CI trigger can be exercised.

- [X] T001 Initialize a local git repository (`git init`), create `main` and `develop` branches, and commit the current working tree as the initial commit. **Local only** — do not add/push to a remote, and do not create the actual GitHub repository, without explicit user confirmation first (a remote push is a shared-state, hard-to-reverse action per the operating guidelines)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The two new CLI commands (`package`, `validate-version`) and the underlying
`versioning` module — fully tested Python that every story's CI job wiring calls into — plus the
generic (not-yet-story-specialized) trigger/build wiring all three stories build on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 Create `src/wh40k_cheatsheet/versioning.py`: `SEMVER_PATTERN` (the canonical SemVer 2.0.0 regex, research.md §3), `parse_release_branch(branch: str) -> str | None`, `is_valid_semver(version: str) -> bool`, `is_prerelease(version: str) -> bool`, `read_project_version(project_root: Path) -> str` (reads `pyproject.toml`'s `[project].version` via `tomllib`), and `VersionError(RuntimeError)` — all with Google-style docstrings per the `008` gate (data-model.md §1)
- [X] T003 [P] Add `package_all(config: ProjectConfig, paths: Paths, dist_dir: Path) -> list[Path]` to `src/wh40k_cheatsheet/pipeline.py`: iterates `config.list_editions()`, calls `generate(config, paths, edition_id)` per edition, copies each `GeneratedDocument.pdf_path` to `dist_dir / f"{edition_id}-{language}.pdf"`, propagating any failure immediately (data-model.md §2; research.md §2)
- [X] T004 Add the `package` subcommand to `src/wh40k_cheatsheet/cli.py`: `_cmd_package(args)` calling `package_all`, with a `--dist-dir` flag (default `dist`) alongside the existing `--project-root`; register it in `build_parser()` (depends on T003; contracts/cli-package-command.md)
- [X] T005 Add the `validate-version` subcommand to `src/wh40k_cheatsheet/cli.py`: `_cmd_validate_version(args)` taking a positional `branch` argument, calling `parse_release_branch`/`is_valid_semver`/`read_project_version`, raising `VersionError` naming both values on mismatch or the malformed value on invalid SemVer, printing the version and exiting `0` on success or on a non-release/hotfix branch (no-op message); add `VersionError` to `KNOWN_ERRORS` (depends on T002; contracts/cli-validate-version-command.md)
- [X] T006 [P] `tests/unit/test_versioning.py`: `parse_release_branch` for `release/*`, `hotfix/*`, and non-matching branch names; `is_valid_semver` accepting plain/pre-release/build-metadata versions and rejecting malformed ones (`1.2`, `release/foo`, leading zeros); `is_prerelease` true/false cases; `read_project_version` against a temp `pyproject.toml` (depends on T002)
- [X] T007 [P] `tests/integration/test_package_command.py`: real `11e` content stages `dist/11e-en.pdf` and `dist/11e-de.pdf`; a synthetic second edition (reusing `test_multi_edition.py`'s pattern) proves editions aren't hardcoded; a deliberately broken edition's content causes the command to fail non-zero with no complete `dist/` presented as successful (depends on T003, T004; contracts/cli-package-command.md G1–G4, F1)
- [X] T008 [P] `tests/integration/test_validate_version_command.py`: a branch matching `pyproject.toml`'s current version succeeds and prints it; a non-release/hotfix branch name is a no-op success; a malformed version and a mismatched version each fail with exit `1` and a message naming the relevant value(s) (depends on T005; contracts/cli-validate-version-command.md G1–G4)
- [X] T009 In `.github/workflows/quality.yml`, broaden triggers: `push.branches` → `["feature/**", "develop", "release/**", "hotfix/**", "main"]`; `pull_request.branches` → `[develop, main]` (contracts/ci-workflow.md T1/T2)
- [X] T010 Add a `build` job to `.github/workflows/quality.yml`: checkout, native WeasyPrint deps + `astral-sh/setup-uv@v3` + `uv sync --locked` (same steps as `check`), then `uv run wh40k-cheatsheet package` — runs on every triggering event, no artifact upload yet, no `validate-version` gating yet (depends on T004, T009; contracts/ci-workflow.md J3, generic slice)

**Checkpoint**: `package`/`validate-version` are fully implemented and tested locally; CI's `check`
and `build` jobs both run on every GitFlow branch type.

---

## Phase 3: User Story 1 - Publish a finished release automatically (Priority: P1) 🎯 MVP

**Goal**: Merging a `release/X.Y.Z` or `hotfix/X.Y.Z` branch into `main` automatically builds every
edition/language and publishes them as a single, correctly-versioned, idempotently-updatable
GitHub Release — with zero manual build or upload steps.

**Independent Test**: Set `pyproject.toml`'s version to `1.2.0`, push a `release/1.2.0` branch, and
merge it into `main`. Confirm a GitHub Release tagged `v1.2.0` appears with one PDF per declared
edition/language, with no manual step.

### Implementation for User Story 1

- [X] T011 [US1] Extend the `build` job (T010) in `.github/workflows/quality.yml` with an `actions/upload-artifact@v4` step uploading `dist/*.pdf` as `cheatsheet-pdfs`, conditioned `if: github.ref_name == 'main'` (main-only for now — US3 broadens this) (depends on T010; contracts/ci-workflow.md J4, main-only slice)
- [X] T012 [US1] Add a `publish-release` job to `.github/workflows/quality.yml`: `if: github.ref == 'refs/heads/main'`, `needs: [check, build]`, job-scoped `permissions: contents: write`; steps: checkout, `actions/download-artifact@v4` (name `cheatsheet-pdfs`, path `dist`), compute `version`/`tag`/prerelease-flag via `uv run python -c "..."` calling `versioning.read_project_version`/`is_prerelease`, then `gh release view "$TAG"` → `gh release upload --clobber` (exists) or `gh release create ... --target "$GITHUB_SHA" [--prerelease]` (doesn't exist) (depends on T002, T011; contracts/ci-workflow.md J5/J6, P1–P6; research.md §4/§5)
- [ ] T013 [US1] [DEFERRED — requires a real GitHub remote] Manually verify quickstart.md Part 2 steps 1 (feature branch push → no publish), 4 (release branch merged to `main` → `v0.2.0` release published with correct assets), and 5 (re-running the same commit updates assets in place, no duplicate/error) against a real GitHub remote (depends on T012)

**Checkpoint**: MVP — merging a release/hotfix branch into `main` reliably, automatically, and
idempotently publishes a correct GitHub Release.

---

## Phase 4: User Story 2 - Catch build-breaking changes on every branch (Priority: P2)

**Goal**: Every push/PR across every GitFlow branch type gets the quality gate *and* a full
edition/language build — and publishing structurally never happens off `main`.

**Independent Test**: Push a change to a `feature/*` branch that breaks generation for one
edition/language. Confirm CI fails on that push, without needing a release branch.

### Implementation for User Story 2

- [ ] T014 [US2] [DEFERRED — requires a real GitHub remote] Manually verify quickstart.md Part 2 step 1 against a real GitHub remote: a `feature/*` push runs `check` and `build` (T009/T010), and confirm (by inspecting the Actions run) that neither `validate-version` nor `publish-release` ran for it — the latter is already structurally guaranteed by `publish-release`'s `if: ref == main` (T012), so this task is verification, not new code (depends on T010, T012)
- [X] T015 [US2] [P] Add a "Continuous Integration" section to `README.md` documenting the GitFlow branch → CI behavior matrix (data-model.md §4): which branches get `check`/`build`/`validate-version`/artifact-upload/`publish-release`, and a link to `specs/012-gitflow-release-pipeline/contracts/ci-workflow.md`

**Checkpoint**: Every GitFlow branch type reliably gets build-breaking-change feedback; publishing
remains structurally confined to `main`.

---

## Phase 5: User Story 3 - Inspect an in-progress release build before it ships (Priority: P3)

**Goal**: Pushes to `release/*`/`hotfix/*` branches produce a downloadable build artifact (gated on
version validation), without ever appearing on the public GitHub Releases page.

**Independent Test**: Push a commit to a `release/X.Y.Z` branch. Confirm the CI run offers a
downloadable artifact with every edition/language PDF, and confirm no GitHub Release appears.

### Implementation for User Story 3

- [X] T016 [US3] Add a `validate-version` job to `.github/workflows/quality.yml`: `if: startsWith(github.head_ref || github.ref_name, 'release/') || startsWith(github.head_ref || github.ref_name, 'hotfix/')`; steps: checkout, setup-uv, `uv sync --locked`, `uv run wh40k-cheatsheet validate-version "${{ github.head_ref || github.ref_name }}"` (depends on T005, T009; contracts/ci-workflow.md J2)
- [X] T017 [US3] Gate the `build` job (T010) on `validate-version` (T016) only when the ref is `release/**`/`hotfix/**`, using GitHub Actions' documented "optional prerequisite" `needs:`/`if: always() && ...` pattern (research.md §4), so a version failure prevents `build` from running on those branches (FR-004's "build no PDFs") (depends on T010, T016; contracts/ci-workflow.md J3, full)
- [X] T018 [US3] Broaden the artifact-upload step's condition (T011, currently `main`-only) in `.github/workflows/quality.yml` to `if: github.ref_name == 'main' || startsWith(github.ref_name, 'release/') || startsWith(github.ref_name, 'hotfix/')` (depends on T011; contracts/ci-workflow.md J4, full)
- [ ] T019 [US3] [DEFERRED — requires a real GitHub remote] Manually verify quickstart.md Part 2 steps 2 (release branch push → downloadable artifact, no public release), 3 (version mismatch → `validate-version` fails, `build` skipped), 6 (hotfix branch behaves identically), and 7 (pre-release version → GitHub Release marked "Pre-release" once merged) against a real GitHub remote (depends on T017, T018, T012)

**Checkpoint**: All three user stories complete — the full GitFlow CI/CD pipeline is operational.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: End-to-end validation and documentation.

- [X] T020 Run quickstart.md Part 1 in full (all 6 steps, fully automatable) and Part 2 to the extent a test GitHub remote is available; confirm expected outcomes — Part 1 fully verified locally; Part 2 deferred (no GitHub remote in this environment)
- [X] T021 [P] Add a "Versioning & releases" section to `README.md`: the `release/X.Y.Z`/`hotfix/X.Y.Z` branch-naming convention, that `pyproject.toml`'s version must match, the `package`/`validate-version` CLI commands, and a link to `specs/012-gitflow-release-pipeline/contracts/cli-package-command.md` and `cli-validate-version-command.md`
- [X] T022 [P] Run `uv run poe check` (full gate: format, lint, security, types, tests) to confirm the new module/commands introduce no regressions — all gates pass, 193/193 tests. (`test_list_logging.py`/`test_list_revisions.py` — features 003/004 — were made robust to any number of declared editions rather than assuming exactly one, after a new "10e" edition appeared in the working tree during this session broke their exact-output assertions; the user confirmed this fix)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately. Nothing else strictly requires T001 to
  exist as code (the Python/CLI tasks don't need git), but the workflow-verification tasks
  (T013/T014/T019/T020 Part 2) do need a real repository to push to.
- **Foundational (Phase 2)**: Depends on Setup only loosely (see above) — BLOCKS all three user
  stories. Contains the entire tested Python surface plus the generic trigger/build wiring.
- **User Story 1 (Phase 3)**: Depends on Foundational. The MVP.
- **User Story 2 (Phase 4)**: Depends on Foundational; T014 also depends on US1's T012 (verifying
  the "never publishes off main" guarantee that T012 itself establishes).
- **User Story 3 (Phase 5)**: Depends on Foundational and on US1's T011 (T018 extends the same
  condition) and T012 (T019's pre-release verification needs publishing to exist).
- **Polish (Phase 6)**: Depends on all three stories being complete.

### Parallel Opportunities

- **Foundational**: T003 is independent of T002; T006/T007/T008 are all independent of each other
  once their respective implementation tasks land.
- **US2**: T015 (README) has no code dependency, parallel to T014.
- **Polish**: T021 and T022 are independent of each other and of T020.

---

## Parallel Example: Foundational tests

```bash
Task: "Unit tests for versioning.py in tests/unit/test_versioning.py"
Task: "Integration tests for the package command in tests/integration/test_package_command.py"
Task: "Integration tests for the validate-version command in tests/integration/test_validate_version_command.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001 — local git init).
2. Complete Phase 2: Foundational (T002–T010) — CRITICAL; the entire tested Python surface plus
   generic CI wiring.
3. Complete Phase 3: User Story 1 (T011–T013).
4. **STOP and VALIDATE**: merging a real `release/X.Y.Z` branch into `main` publishes a correct
   GitHub Release with zero manual steps.
5. Demonstrable MVP — automated, versioned release publishing.

### Incremental Delivery

1. Setup + Foundational → tested CLI commands + every-branch build/quality checks exist.
2. US1 → automated release publishing on merge to `main` (MVP!) → validate → demo.
3. US2 → confirms/documents the every-branch safety net (mostly already true by construction).
4. US3 → downloadable pre-release artifacts + version-mismatch gating during stabilization.
5. Polish → full quickstart validation + docs + regression gate.

---

## Notes

- [P] = different files or independent verification steps, no dependencies.
- [Story] label maps each task to its user story for traceability.
- T014 and T019 are verification-only tasks (no new code) precisely because the guarantees they
  check were already established structurally by earlier tasks (T012's `if: ref == main`,
  T017/T018's conditions) — this mirrors the "Foundational already delivers the behavior, the story
  phase verifies it" shape used in prior features (e.g. `010`), just spread across three stories
  instead of one.
- Commit after each task or logical group; stop at any checkpoint to validate independently.

---

## Phase 7: Amendment (2026-09-14) — Auto-Bump `pyproject.toml`/`uv.lock` on Release/Hotfix Push

**Purpose**: Removes the last manual step in cutting a release — hand-editing `pyproject.toml`
(and re-running `uv lock`) to match a `release/*`/`hotfix/*` branch's name before pushing it. See
spec.md's 2026-09-14 amendment (FR-013), contracts/cli-validate-version-command.md's `--fix` flag,
and contracts/ci-workflow.md's updated J2/J5/P7/P8.

**Goal**: A push to a release/hotfix branch whose `pyproject.toml` doesn't yet match the branch's
version gets corrected automatically (`pyproject.toml` rewritten, `uv.lock` re-locked, both
committed and pushed) instead of failing; a pull request from that branch still only verifies.

- [X] T023 Add `write_project_version(project_root: Path, version: str) -> bool` to `src/wh40k_cheatsheet/versioning.py` — a scoped, `[project]`-table-only text substitution of the `version = "..."` line, returning whether it actually changed anything (data-model.md §1; research.md §6)
- [X] T024 Add a `--fix` flag to the `validate-version` subparser and update `_cmd_validate_version` in `src/wh40k_cheatsheet/cli.py`: on a mismatch, call `write_project_version` and print `"<old> -> <new>"` instead of raising, only when `--fix` is set (contracts/cli-validate-version-command.md G5; depends on T023)
- [X] T025 [P] Unit tests for `write_project_version` in `tests/unit/test_versioning.py`: rewrites the version line; preserves every other byte of the file (comments, other tables, a same-named `version` key elsewhere); is a byte-for-byte no-op when already matching; raises `VersionError` for a missing file or missing `[project].version` (depends on T023)
- [X] T026 [P] Integration tests for `validate-version --fix` in `tests/integration/test_validate_version_command.py`: rewrites on mismatch and prints the old/new pair; no-ops when already matching; still raises on a malformed branch version; still a no-op on a non-release branch (depends on T024)
- [X] T027 Update `.github/workflows/quality.yml`'s `validate-version` job: add `permissions: contents: write`; branch its steps on `github.event_name` — `pull_request` keeps the original verify-only call, `push` calls `--fix`, conditionally re-locks (`uv lock` only if `pyproject.toml` changed), and commits + pushes both files with a `[skip ci]` message when either changed (contracts/ci-workflow.md J2/P7/P8; depends on T024)
- [X] T028 [P] Add `ref: ${{ github.ref_name }}` to `publish-prerelease`'s checkout step in `.github/workflows/quality.yml`, so it observes T027's auto-fix commit instead of the stale pre-push SHA (contracts/ci-workflow.md J5)
- [X] T029 [P] Update `docs/DEVELOPMENT.md`'s "Continuous Integration" table and "Versioning & releases" section for the new auto-fix behavior and the `--fix` flag
- [X] T030 Run `uv run poe check` and confirm every gate passes, including the new tests

**Checkpoint**: Pushing a `release/X.Y.Z` branch with a stale `pyproject.toml` self-corrects; a
subsequent pull request into `main`/`develop` finds nothing left to fix.

---

## Phase 8: Bug Fix (2026-09-14, two rounds) — `publish-release` Never Ran on `main`

**Purpose**: Reported directly against two real `main`-branch CI runs, in succession: `check` and
`build` both succeeded, but `publish-release` stayed skipped anyway, meaning no GitHub Release was
ever published from any merge to `main` since this feature shipped. Two independent GitHub Actions
defaults compounded (bare `success()`'s transitivity, and a separate implicit skip-propagation
default that only `always()` overrides) — fixing the first alone still left it skipped on the very
next real run. See spec.md's 2026-09-14 bug-fix note and `contracts/ci-workflow.md`'s P9 /
"Known boundaries" for the full mechanism.

- [X] T031 (round 1) Change `publish-release`'s `if:` in `.github/workflows/quality.yml` from `success() && github.ref == 'refs/heads/main'` to `needs.check.result == 'success' && needs.build.result == 'success' && github.ref == 'refs/heads/main'`
- [X] T032 [P] (round 1) Apply the same fix to `publish-prerelease`'s `if:` for consistency (not actually broken by this bug — `validate-version` genuinely runs, not skips, for the release/hotfix branches it fires on — but this prevents the same failure mode if a future conditionally-skipped job is added to the graph)
- [X] T033 [P] (round 1) Document the bug and fix in `contracts/ci-workflow.md` (new P9 guarantee, updated J6, new "Known boundaries" section) and `spec.md` (new "Bug fix 2026-09-14" note)
- [X] T034 (round 2 — round 1 confirmed insufficient against a second real main-branch run) Prepend `always() &&` to both `publish-release`'s and `publish-prerelease`'s `if:` in `.github/workflows/quality.yml`, ANDed with (not replacing) round 1's explicit `needs.*.result` checks — mirroring `build`'s own already-correct `if: always() && (needs.validate-version.result == 'success' || ...)` pattern in the same file
- [X] T035 [P] Update `contracts/ci-workflow.md` (J6, P9, "Known boundaries") and `spec.md`'s bug-fix note for round 2's corrected, complete fix

**Checkpoint**: A `main`-branch push where `check`/`build` both succeed now actually reaches
`publish-release` and publishes/updates the GitHub Release — verify on the next real merge to
`main`, since neither of these GitHub Actions job-scheduling interactions is practically
reproducible in a local/unit test (they're artifacts of GitHub's own scheduler, not this
project's code).
