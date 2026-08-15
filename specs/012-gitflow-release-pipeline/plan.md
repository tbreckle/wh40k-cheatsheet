# Implementation Plan: GitFlow CI/CD Release Pipeline

**Branch**: `012-gitflow-release-pipeline` | **Date**: 2026-08-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/012-gitflow-release-pipeline/spec.md`

## Summary

Wire the repository's CI/CD around GitFlow branch types (`feature/*`, `develop`, `release/*`,
`hotfix/*`, `main`) and SemVer. Two new, well-tested Python CLI commands carry the actual logic —
`package` (build every declared edition/language, staged flat as `<edition>-<language>.pdf` into
`dist/`) and `validate-version` (parse a `release/X.Y.Z`/`hotfix/X.Y.Z` branch name, validate it's
SemVer 2.0.0, and confirm it matches `pyproject.toml`'s version) — so the GitHub Actions workflow
YAML stays a thin orchestration layer over pytest-covered application code, consistent with how
every other pipeline capability in this project is built and tested. A single workflow file adds
three jobs (`validate-version`, `build`, `publish-release`) alongside the existing `quality` job,
wired with `needs:` so publishing only ever happens after quality + build succeed on a `main`-branch
commit, using the already-built artifact rather than rebuilding. Release/hotfix branch pushes get a
downloadable workflow artifact only; publishing to GitHub Releases (via the pre-installed `gh` CLI,
no new third-party Action) happens exclusively from `main`, idempotently updating an existing
release's assets if one already exists for that tag.

## Technical Context

**Language/Version**: Python 3.12+ (shared with features 001–011; no change). SemVer/branch-name
validation uses the stdlib `re` module; the project's own version is read from `pyproject.toml` via
the stdlib `tomllib` (Python 3.11+) — no new runtime dependency.

**Primary Dependencies**: None new in `pyproject.toml`. The CI workflow itself uses only
already-established, official/pre-installed tooling: `actions/checkout@v4`, `astral-sh/setup-uv@v3`
(both already in `quality.yml`), `actions/upload-artifact@v4` / `actions/download-artifact@v4`
(official GitHub actions), and the `gh` CLI (pre-installed on GitHub-hosted runners) for creating
and updating GitHub Releases — deliberately not a third-party release-publishing Action, avoiding an
unjustified new dependency per the constitution's Additional Constraints.

**Storage**: N/A — build output is transient (`dist/*.pdf`, a workflow-run artifact, and GitHub
Release assets); no persistent storage introduced.

**Testing**: pytest. New `tests/unit/test_versioning.py` covers `validate-version`'s logic directly
(branch-name parsing for both `release/` and `hotfix/` prefixes, SemVer 2.0.0 acceptance/rejection
including pre-release and build-metadata suffixes, version-mismatch detection, and non-release
branch names being rejected/ignored as appropriate) — pure functions, no I/O, fast and exhaustive.
New `tests/integration/test_package_command.py` covers the `package` CLI command against real `11e`
content: every declared edition/language lands in the output directory named
`<edition_id>-<language>.pdf`, adding a synthetic second edition (the existing pattern from
`test_multi_edition.py`) proves it isn't hardcoded to `11e`, and a deliberately broken edition
proves the command fails loudly (no partial `dist/`) rather than silently omitting the broken one —
matching the spec's "all editions/languages or nothing" edge case. The GitHub Actions workflow YAML
itself is not executable under pytest; it's validated by (a) being pure orchestration over the two
CLI commands above, each independently tested, and (b) manual construction against GitHub's
documented syntax, cross-checked in quickstart.md's job-graph walkthrough. This is the same
division of responsibility the project already uses for `quality.yml` (thin YAML over `poe check`).

**Target Platform**: GitHub Actions on `ubuntu-latest` runners (matching the existing
`quality.yml`), publishing to the same repository's GitHub Releases.

**Project Type**: Single project. Adds two CLI subcommands (`package`, `validate-version`) to the
existing `src/wh40k_cheatsheet/cli.py`, a small new `src/wh40k_cheatsheet/versioning.py` module, a
`package_all` pipeline function in `src/wh40k_cheatsheet/pipeline.py`, and extends
`.github/workflows/quality.yml` (renamed conceptually to a multi-job CI/CD workflow; the existing
`check` job is unchanged, three jobs are added).

**Performance Goals**: Not performance-sensitive — CI wall-clock time matters for developer
feedback loop, but no numeric budget was specified; reusing the `build` job's own artifact for
`publish-release` (rather than rebuilding on `main`) avoids doubling generation time in the
publish path.

**Constraints**: Publishing (FR-007) MUST only run after the same commit's quality gate and build
both succeed (FR-009) — enforced via GitHub Actions' `needs:` job dependency graph, which
automatically skips a dependent job if any of its `needs:` failed, rather than a manual check.
Version validation (FR-004) MUST run, and must gate the build, only on `release/*`/`hotfix/*`
branches — other branch types have no version to validate. A GitHub Release MUST never be created
directly from a push to `release/*`/`hotfix/*` (FR-006) — the `publish-release` job's trigger is
scoped to `main` only, structurally, not by a runtime check that could be bypassed.

**Scale/Scope**: One project currently declares one edition (`11e`) × two languages (`en`, `de`) =
2 PDFs per build; the design must not hardcode that (FR-002/SC-005) — `package_all` discovers
editions/languages from the already-existing `ProjectConfig.list_editions()` /
`Edition.languages`, the same source `list_inventory` already uses.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment |
|-----------|------------|
| I. Code Quality | **Satisfied.** The two new CLI commands follow the exact shape of `generate`/`list` (thin `_cmd_*` handlers over typed pipeline/versioning functions), typed, single-responsibility, Google-style docstrings per the `008` gate. The GitHub Actions YAML stays declarative orchestration, not a place where logic accumulates. |
| II. Testing Standards (NON-NEGOTIABLE) | **Satisfied by design.** `validate-version`'s branch-parsing/SemVer/mismatch logic and `package`'s all-editions/all-languages build are both pure, pytest-covered Python — including the "fails loudly, no partial output" boundary case the spec calls out explicitly. |
| III. User Experience Consistency | **Satisfied.** New commands reuse the existing `--project-root`/`-v` conventions and `KNOWN_ERRORS` → clear-message → exit-1 pattern already established by `generate`/`list`; no new interaction pattern introduced. |
| IV. Performance Requirements | **Satisfied.** No lookup/interactive-latency path touched; this is a build/release pipeline, and the design explicitly avoids redundant rebuilding (reuses the `build` job's artifact for publishing). |
| Additional Constraints & Standards | **Satisfied.** No new runtime dependency; the `gh` CLI and official GitHub actions are pre-installed/already-adopted tooling, not new supply-chain surface. Release provenance is inherently traceable — each release is tied to a specific `main` commit and the `pyproject.toml` version it carried. |
| Development Workflow & Quality Gates | **Satisfied — and this feature is what makes the gate meaningful across GitFlow.** The existing `poe check` gate now runs on every GitFlow branch type, not just `main`/PRs-to-main; publishing is structurally impossible without it passing first. |

**Verdict**: PASS. No violations; Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/012-gitflow-release-pipeline/
├── plan.md                  # This file (/speckit-plan command output)
├── research.md               # Phase 0 output (/speckit-plan command)
├── data-model.md             # Phase 1 output (/speckit-plan command)
├── quickstart.md             # Phase 1 output (/speckit-plan command)
├── contracts/
│   ├── cli-package-command.md
│   ├── cli-validate-version-command.md
│   └── ci-workflow.md
└── tasks.md                    # Phase 2 (/speckit-tasks — NOT created here)
```

### Source Code (repository root) — changes to existing/new files

```text
src/wh40k_cheatsheet/versioning.py                # NEW
    # parse_release_branch(branch: str) -> str | None   — strips "release/"/"hotfix/"
    #   prefix, returns the raw version string or None if the branch isn't a
    #   release/hotfix branch
    # SEMVER_PATTERN — compiled regex, the canonical SemVer 2.0.0 grammar
    # is_valid_semver(version: str) -> bool
    # is_prerelease(version: str) -> bool               — has a pre-release component
    # VersionError(RuntimeError)                        — malformed/mismatched version

src/wh40k_cheatsheet/pipeline.py
    # ADDED: package_all(config, paths, dist_dir) -> list[Path]
    #   iterates config.list_editions() (every declared edition, every language,
    #   reusing generate() per edition), copies each GeneratedDocument.pdf_path into
    #   dist_dir / f"{edition_id}-{language}.pdf"; propagates any failure (no partial
    #   dist/ — matches the spec's all-or-nothing edge case)

src/wh40k_cheatsheet/cli.py
    # ADDED: `package` subcommand — _cmd_package(args): calls package_all, prints
    #   one line per staged file
    # ADDED: `validate-version` subcommand — _cmd_validate_version(args): calls
    #   versioning.parse_release_branch + is_valid_semver + compares against
    #   pyproject.toml's version (read via tomllib); prints the version on success
    # KNOWN_ERRORS gains VersionError

tests/unit/test_versioning.py                       # NEW
tests/integration/test_package_command.py            # NEW

.github/workflows/quality.yml                        # CHANGED (jobs added; existing
    # `check` job's steps are otherwise untouched)
    # Trigger broadened: push branches ['feature/**','develop','release/**',
    #   'hotfix/**','main'], pull_request branches [develop, main]
    # ADDED job `validate-version`: only on release/**|hotfix/** refs; runs
    #   `uv run wh40k-cheatsheet validate-version <branch>`
    # ADDED job `build`: all branches; needs validate-version only when the ref is
    #   release/**|hotfix/**; runs `uv run wh40k-cheatsheet package`; uploads
    #   dist/*.pdf as workflow artifact `cheatsheet-pdfs` only when the ref is
    #   release/**|hotfix/**|main
    # ADDED job `publish-release`: only on the main ref; needs: [check, build];
    #   downloads the `cheatsheet-pdfs` artifact, reads pyproject.toml's version,
    #   creates or updates (gh release view/create/upload --clobber) a GitHub
    #   Release tagged vX.Y.Z with those assets, marked prerelease if the version
    #   contains "-"; job-scoped `permissions: contents: write`
```

**Structure Decision**: Single project, same layout as every prior feature. The two new CLI
commands + one new small module are the only Python surface added; everything else is workflow
YAML orchestrating them, mirroring how `quality.yml` already orchestrates `poe check` rather than
embedding logic in YAML/bash.

## Complexity Tracking

> No constitution violations. Section intentionally left empty.
