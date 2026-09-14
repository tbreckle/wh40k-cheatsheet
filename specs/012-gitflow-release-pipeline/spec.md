# Feature Specification: GitFlow CI/CD Release Pipeline

**Feature Branch**: `012-gitflow-release-pipeline`

**Created**: 2026-08-15

**Status**: Draft

**Input**: User description: "CI pipeline shall support GitFlow. Versioning is done using SemVer.
Builds shall build all editions and languages available. Actions shall deploy from release branch
to Github Releases."

## Clarifications

### Session 2026-08-15

- Q: When should the pipeline actually publish a GitHub Release from a release branch? → A: Every
  push to a `release/*` (or `hotfix/*`) branch produces a downloadable build artifact from that CI
  run, but does **not** create or update a public GitHub Release. A GitHub Release is only
  published once that branch is merged into `main` (GitFlow's canonical "release finished" point).
- Q: What determines the SemVer version number that gets published? → A: The release/hotfix
  branch's own name encodes the version (`release/X.Y.Z` / `hotfix/X.Y.Z`), matching GitFlow's
  long-standing naming convention. CI validates it's well-formed SemVer and that it exactly matches
  `pyproject.toml`'s `[project].version` field, failing the branch's pipeline if they disagree.
- Q: Should `hotfix/*` branches also auto-publish to GitHub Releases, the same as `release/*`
  branches? → A: Yes — hotfix branches use the identical version-validation, build, and (on merge
  to `main`) publish mechanism as release branches, since a hotfix is itself a real patch release.

### Session 2026-09-03

- Q: Should a push directly to a `release/*`/`hotfix/*` branch publish anything to the public
  GitHub Releases page, rather than only producing a downloadable CI artifact? → A: Yes — this
  supersedes the first 2026-08-15 clarification. Every push to a `release/*` or `hotfix/*` branch
  now creates or updates a GitHub Release tagged with that branch's version, always marked
  **pre-release** regardless of whether the version string itself carries a SemVer pre-release
  component. When that branch is later merged into `main`, the same tag is updated in place and
  promoted: un-marked as pre-release unless the version string still carries its own pre-release
  component (FR-010 still governs the final state).

### Session 2026-09-14

- Q: FR-004 currently makes CI *fail* a release/hotfix branch's pipeline if `pyproject.toml`'s
  version disagrees with the branch name, requiring whoever cuts the release to hand-edit
  `pyproject.toml` (and `uv.lock`, which embeds the same version for this project's own,
  editable-installed package) to match *before* pushing. Should CI instead write the correct
  version itself? → A: Yes, but only on a direct push to the branch, and only using the version
  already encoded in that branch's own name (no GitVersion-style history/commit-message
  inference) — the branch name remains the single, human-chosen source of truth for the target
  version; CI's job is purely mechanical: copy that value into `pyproject.toml`, run `uv lock` so
  `uv.lock` stays consistent, and commit + push both back to the branch. A pull request from that
  branch into `develop`/`main` keeps the original strict, read-only validation (FR-004 unchanged
  for that event) as a safety net — it should never find a mismatch, since the push above already
  fixed it, and a mismatch there would mean something bypassed that automation. `main`'s own
  version is unaffected by this amendment: it is still whatever version the merged release/hotfix
  branch carried (already fixed by this mechanism before the merge), never separately bumped.

### Bug fix 2026-09-14 (reported against a real `main`-branch CI run)

`publish-release` never actually ran on `main`, in any run, since this feature originally shipped:
its `if: success() && github.ref == 'refs/heads/main'` used the bare `success()` status-check
function, which evaluates across a job's *entire transitive* `needs:` chain — and `build` (one of
`publish-release`'s two direct `needs:`) itself depends on `validate-version`, which is *always*
skipped on `main` by design (FR-003/FR-004 only ever apply to `release/*`/`hotfix/*`). `success()`
saw that upstream skip and returned `false` unconditionally, so `publish-release` was skipped on
every single push to `main`, regardless of whether `check`/`build` passed — silently defeating User
Story 1, this feature's entire core deliverable, despite every individual job reporting green.
Fixed by checking `needs.check.result == 'success' && needs.build.result == 'success'` directly
instead of bare `success()`, in both `publish-release` and `publish-prerelease` (the latter wasn't
actually broken today, since `validate-version` genuinely runs — not skips — on the release/hotfix
branches `publish-prerelease` fires for, but is fixed the same way for consistency and to not
reintroduce this exact failure mode the next time a conditionally-skipped job is added to the
graph). See `contracts/ci-workflow.md`'s P9 and "Known boundaries" section.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Publish a finished release automatically (Priority: P1)

A maintainer finishes stabilizing a `release/X.Y.Z` (or `hotfix/X.Y.Z`) branch and merges it into
`main`. Without running any command or uploading anything by hand, every declared edition and
language combination is built and published as a single, correctly-versioned GitHub Release, with
one clearly-named PDF per (edition, language) attached.

**Why this priority**: This is the core deliverable — everything else in this feature exists to
make this moment safe and automatic. Without it, the feature has no user-visible value.

**Independent Test**: Set `pyproject.toml`'s version to `1.2.0`, push a `release/1.2.0` branch, and
merge it into `main`. Confirm a GitHub Release tagged `v1.2.0` appears, containing one PDF per
edition/language declared in the project's configuration, with no manual build or upload step.

**Acceptance Scenarios**:

1. **Given** a `release/1.2.0` branch whose `pyproject.toml` version is `1.2.0`, **When** it is
   merged into `main`, **Then** a GitHub Release tagged `v1.2.0` is published, containing one PDF
   asset for every edition/language combination declared in the project's configuration.
2. **Given** the same scenario with a `hotfix/1.2.1` branch instead, **When** it is merged into
   `main`, **Then** a GitHub Release tagged `v1.2.1` is published the same way.
3. **Given** a release version containing a pre-release component (e.g. `1.3.0-rc.1`), **When** it
   is published, **Then** the resulting GitHub Release is marked as a pre-release; a version with
   no pre-release component is published as a full release.
4. **Given** a merge to `main` whose commit fails the quality gate or the full build (any edition
   or language fails to generate), **When** that happens, **Then** no GitHub Release is published
   for that commit.
5. **Given** a GitHub Release for a given version's tag already exists at merge time (e.g., the
   merge event is re-run), **When** publishing runs again, **Then** its assets are updated in
   place rather than the pipeline failing or a duplicate release being created.

---

### User Story 2 - Catch build-breaking changes on every branch (Priority: P2)

A contributor pushes to a `feature/*` branch, or the maintainer pushes to `develop`, a `release/*`
branch, or a `hotfix/*` branch. In every case, CI runs the project's existing quality gate *and*
attempts to build every declared edition and language, so a change that breaks generation for any
one of them is caught immediately — long before anyone attempts a release.

**Why this priority**: Broadens the safety net from "only checked at release time" to "checked on
every single change," which is where most build breaks are actually introduced and are cheapest to
fix.

**Independent Test**: Push a change to a `feature/*` branch that breaks PDF generation for one
edition/language (e.g., malformed content). Confirm CI fails on that push, identifying the failure,
without needing to reach a release branch first.

**Acceptance Scenarios**:

1. **Given** any push or pull request on a `feature/*`, `develop`, `release/*`, `hotfix/*`, or
   `main` branch, **When** CI runs, **Then** it runs the existing quality gate (lint, format, type
   check, security scan, tests) and additionally builds every edition/language combination
   declared in the project's configuration.
2. **Given** a new edition or language is added to the project's configuration, **When** CI next
   runs on any branch, **Then** it is automatically included in the build step with no change to
   the CI pipeline itself required.
3. **Given** a `feature/*` or `develop` branch push, **When** CI completes successfully, **Then**
   no GitHub Release is published — publishing only ever results from a release/hotfix branch
   merging into `main`.

---

### User Story 3 - Inspect an in-progress release build before it ships (Priority: P3)

While stabilizing a `release/*` or `hotfix/*` branch — before it's ready to merge into `main` — the
maintainer wants to download and inspect the exact PDFs that branch currently produces, to verify
the release is correct. Those in-progress builds are published to the Releases page too, always
clearly marked pre-release, so the maintainer (or an early tester) can grab them the same way they'd
grab any other release, without mistaking one for a finished release.

**Why this priority**: A convenience and safety check during stabilization; valuable but not
essential to the pipeline's core purpose, and depends on User Story 2's build step already
existing.

**Independent Test**: Push a commit to a `release/X.Y.Z` branch. Confirm the CI run for that push
publishes (or updates) a GitHub Release tagged `vX.Y.Z`, marked pre-release, containing every
edition/language PDF.

**Acceptance Scenarios**:

1. **Given** a push to a `release/*` or `hotfix/*` branch, **When** CI completes successfully,
   **Then** the built PDFs (every edition/language) are attached to that CI run as a downloadable
   artifact, **and** a GitHub Release tagged with that branch's version is created or updated on the
   repository's Releases page, marked pre-release.
2. **Given** a second push to the same `release/*`/`hotfix/*` branch, **When** CI completes, **Then**
   the existing pre-release for that version is updated in place (assets replaced) rather than a
   duplicate release being created.

---

### Edge Cases

- What happens if a `release/*` or `hotfix/*` branch's name doesn't parse as valid SemVer (e.g.
  `release/foo`, `release/1.2`)? CI fails that branch's pipeline immediately with a clear error,
  before attempting any build.
- What happens if `pyproject.toml`'s version doesn't match the version encoded in the release or
  hotfix branch's name? On a pull request, CI fails immediately with a clear error naming both
  values; nothing is built or published. On a direct push to the branch (2026-09-14 amendment,
  FR-013), CI corrects `pyproject.toml`/`uv.lock` to the branch-name version and commits the fix
  instead of failing — a malformed branch-name version still fails either way, since there is no
  value to write.
- What happens if two people push to the same release/hotfix branch at nearly the same time,
  racing FR-013's auto-commit against another push? The auto-commit push can be rejected as a
  non-fast-forward update, same as any other simultaneous push to the same branch; CI's push step
  is not force-pushed or retried automatically, so this surfaces as an ordinary failed CI run to
  re-run, not silent data loss.
- What happens with two release branches open at once (e.g. `release/1.2.0` and a later
  `release/1.3.0` started before the first ships)? Each is validated and built independently on its
  own pushes; only whichever one(s) are actually merged into `main` ever publish a release — no
  cross-branch interference.
- What happens on the very first push to `main` after this pipeline is adopted? It publishes a
  GitHub Release for whatever version `pyproject.toml` holds at that point — expected behavior, not
  an error, since `main` is only ever expected to receive release/hotfix merges under GitFlow.
- What happens if the build step fails for just one edition/language out of many? The whole build
  step fails (no partial release, no partial artifact) — a release is all-editions-and-languages or
  nothing.
- What happens if a release/hotfix branch is deleted (its release finished, or abandoned) after its
  pre-release was published? The pre-release entry remains on the Releases page — cleaning up
  abandoned pre-releases is a manual maintainer action, out of scope for this feature.
- What happens if a `release/X.Y.Z` branch is merged into `main` and its pre-release already exists
  under tag `vX.Y.Z`? FR-007's publish step updates that same release in place (assets replaced,
  pre-release flag promoted per FR-010) — it is never left marked pre-release after a successful
  merge to `main`, unless the version itself still carries a SemVer pre-release component.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: CI MUST run the project's existing quality gate (lint, format, type check, security
  scan, automated tests) on every push and pull request, across every GitFlow branch type
  (`feature/*`, `develop`, `release/*`, `hotfix/*`, `main`).
- **FR-002**: CI MUST additionally build every edition and every language declared in the
  project's own configuration on every push and pull request, across every GitFlow branch type —
  the set of editions/languages built MUST be discovered from that configuration at build time, not
  hardcoded in the pipeline, so a newly added edition or language is automatically included without
  a pipeline change.
- **FR-003**: A `release/*` or `hotfix/*` branch's name MUST encode its target version as
  `release/X.Y.Z` or `hotfix/X.Y.Z`, where `X.Y.Z` is a valid SemVer 2.0.0 version (optionally with
  a pre-release and/or build-metadata suffix, e.g. `1.3.0-rc.1`).
- **FR-004**: On every pull request from a `release/*` or `hotfix/*` branch (into `develop` or
  `main`), CI MUST validate that the version encoded in the branch name is well-formed SemVer and
  exactly matches the project's package version (`pyproject.toml`'s `[project].version`); CI MUST
  fail that pipeline (build no PDFs, publish nothing) if they disagree or the branch-name version
  is malformed. On a direct push to the branch, FR-013 applies instead.
- **FR-013** (2026-09-14 amendment): On every push directly to a `release/*` or `hotfix/*` branch,
  if the branch-name version is well-formed SemVer but disagrees with `pyproject.toml`'s
  `[project].version`, CI MUST rewrite `pyproject.toml` to the branch-name version, re-run the
  project's dependency lock (`uv.lock`) so it stays consistent with that version, and commit +
  push both files back to the branch — rather than failing, as FR-004 still does for a pull
  request or a malformed branch-name version. `main`'s own version is never bumped by this
  mechanism; it only ever receives whatever version a release/hotfix branch already carries at
  merge time.
- **FR-005**: On every successful push to a `release/*` or `hotfix/*` branch, CI MUST attach the
  built PDFs (every edition/language) to that CI run as a downloadable build artifact.
- **FR-006**: On every successful push directly to a `release/*` or `hotfix/*` branch (not a pull
  request, not `main`), CI MUST create or update a public GitHub Release tagged with that branch's
  version, with one PDF asset attached per (edition, language), always marked GitHub "pre-release"
  regardless of whether the version string itself carries a SemVer pre-release component.
- **FR-007**: When a `release/*` or `hotfix/*` branch is merged into `main`, CI MUST build every
  edition/language combination and publish them to GitHub Releases as a single release, tagged with
  the SemVer version from `pyproject.toml` (e.g. `v1.2.0`), with one PDF asset attached per
  (edition, language) — updating FR-006's pre-release in place if one already exists for that tag.
- **FR-008**: Each release asset's filename MUST identify its edition and language (e.g. include
  the edition id and language code), so a downloader can tell which file is which without opening
  it.
- **FR-009**: Publishing a GitHub Release (FR-006, FR-007) MUST only happen after that same commit's
  quality gate (FR-001) and full build (FR-002) have both succeeded — a release is never published
  from a commit that fails either.
- **FR-010**: At the point a `release/*`/`hotfix/*` branch is merged into `main` (FR-007), a SemVer
  version containing a pre-release component (e.g. `1.3.0-rc.1`) MUST be published as a GitHub
  "pre-release"; a version without one MUST be promoted to a full release, even if a prior push to
  the branch (FR-006) had already marked that tag pre-release.
- **FR-011**: If a GitHub Release for a given version's tag already exists at publish time (FR-006
  or FR-007), CI MUST update its assets in place rather than failing or creating a duplicate release.
- **FR-012**: CI MUST NOT publish a GitHub Release as a result of any push to `feature/*` or
  `develop` branches, nor from a pull request; publishing only ever results from a direct push to a
  `release/*`/`hotfix/*` branch (FR-006, always pre-release) or a merge into `main` (FR-007).

### Key Entities

- **GitFlow Branch**: One of `feature/*`, `develop`, `release/*`, `hotfix/*`, or `main`. Every
  branch type always gets the quality gate + full build (FR-001/FR-002). `release/*`/`hotfix/*`
  branches additionally carry a target version, produce a downloadable artifact (FR-005), and
  publish/update a pre-release GitHub Release on every push (FR-006). `main` promotes that same
  release on a release/hotfix merge (FR-007).
- **SemVer Version**: A `MAJOR.MINOR.PATCH[-prerelease][+build]` string per SemVer 2.0.0. Its
  authoritative source is `pyproject.toml`'s `[project].version`; a release/hotfix branch's name
  must restate the same value for validation (FR-004).
- **Build Artifact**: The complete set of generated PDFs (one per declared edition/language) from a
  single CI run, attached to that run for download. Ephemeral and not publicly listed — distinct
  from a GitHub Release.
- **GitHub Release**: A published, publicly-listed, versioned release on the repository's Releases
  page, tagged `vX.Y.Z`, containing one PDF asset per declared edition/language. Always pre-release
  while its tag's version is still on a `release/*`/`hotfix/*` branch (FR-006); on merge to `main` it
  is promoted to a full release unless its version string itself has a pre-release component
  (FR-010).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of pushes and pull requests, across every GitFlow branch type, run the full
  quality gate and a build of every declared edition/language with zero manual steps.
- **SC-002**: 100% of merges of a `release/*` or `hotfix/*` branch into `main` result in a published
  GitHub Release containing one correctly-named PDF per declared edition/language, with zero manual
  build or upload steps.
- **SC-003**: 100% of version mismatches between a release/hotfix branch name and the project's
  package version are caught by CI before anything is built or published on a pull request; on a
  direct push to the branch, 100% are instead corrected automatically (FR-013) with no manual
  `pyproject.toml`/`uv.lock` edit required to cut a release.
- **SC-004**: A maintainer can download and inspect the exact PDFs a release/hotfix branch
  currently produces at any point during stabilization, without running any local build command,
  via either the CI run's downloadable artifact or the branch's pre-release entry on the public
  Releases page — and that entry is unambiguously marked pre-release, never mistakable for a
  finished release.
- **SC-005**: Adding a new edition or language to the project's configuration requires zero changes
  to the CI pipeline for it to be included in every future build and release.
- **SC-006**: A maintainer can tell, from the GitHub Releases page alone, which published release is
  newest and which (if any) are pre-releases, without reading commit history.

## Assumptions

- The repository is (or will be, as part of adopting this pipeline) hosted on GitHub and uses
  GitHub Actions as its CI/CD platform, consistent with the existing `.github/workflows/quality.yml`
  and the explicit mention of "Github Releases."
- Adopting GitFlow branches (`main`, `develop`, and the `feature/*`/`release/*`/`hotfix/*` naming
  conventions) in the repository itself is a one-time setup step this feature depends on, not a
  behavior the pipeline needs to enforce beyond reacting correctly to those branch names once they
  exist.
- `pyproject.toml`'s `[project].version` is the single authoritative source of the package's
  current SemVer version. As of the 2026-09-14 amendment (FR-013), keeping it (and `uv.lock`)
  updated to match a release/hotfix branch's name is automated by CI on every push to that
  branch — the only manual step left to whoever cuts the release is choosing and naming the
  branch itself; `main`'s version is never separately bumped, only ever inherited from a merged
  release/hotfix branch.
- The branch name remains the sole source of the target version number — this feature
  deliberately does not infer a version bump from commit history or message content (no
  GitVersion-style conventional-commit analysis), keeping the mechanism a simple, predictable
  text substitution rather than a second versioning policy to maintain.
- Release assets are the standard PDFs only (one per edition/language); the optional
  print-friendly variant (feature 011) is not included in release assets by default.
- Enforcing that each new release's version is strictly greater than the previously published one
  is out of scope for this feature — FR-004 validates the version is well-formed and matches
  `pyproject.toml`, not that it's an increase over history.
- "All editions and languages available" means everything declared in `project.yaml` at build
  time — there is no partial/selective release mechanism in scope for this feature.
