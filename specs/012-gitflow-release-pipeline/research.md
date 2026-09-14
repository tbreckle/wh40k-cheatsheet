# Phase 0 Research: GitFlow CI/CD Release Pipeline

No open `[NEEDS CLARIFICATION]` markers remained after `/speckit-specify` — the three genuinely
scope-defining ambiguities (release trigger, version source, hotfix scope) were resolved
interactively before drafting and are recorded in spec.md's Clarifications section. The decisions
below are the technical design choices needed to implement those resolved requirements.

## 1. Where should the "build every edition/language" and "validate the version" logic live?

**Decision**: As two new, independently pytest-covered CLI subcommands — `package` and
`validate-version` — in the existing `wh40k_cheatsheet` package, not as shell/Python scripts living
only inside `.github/`.

**Rationale**: Every existing pipeline capability in this project (`generate`, `list`) is a typed,
tested Python function reachable from a thin CLI handler; the constitution's Testing Standards are
non-negotiable, and CI workflow YAML/bash is not something pytest can exercise. Keeping the actual
logic in the package means it gets the same lint/type/docstring/test gates as everything else, is
independently runnable/debuggable outside CI, and the workflow YAML stays a thin orchestration
layer — exactly the division of responsibility `quality.yml` already uses for `poe check`.

**Alternatives considered**:
- *Bash scripts under `.github/scripts/`*: rejected — SemVer parsing/validation in bash regex is
  fragile and effectively untestable under the project's pytest-based gate; the project has zero
  existing shell scripts, and introducing that pattern for exactly the two places that most need
  correctness (version validation, release asset naming) is the wrong trade-off.
- *Logic inline in the workflow YAML's `run:` steps*: rejected for the same reason, more strongly —
  no test coverage at all, and multi-line bash embedded in YAML is hard to review/maintain.

## 2. How does the "build every edition/language" step discover what to build?

**Decision**: A new `package_all(config, paths, dist_dir)` pipeline function that iterates
`config.list_editions()` — the exact same source `list_inventory` (the `list` command) already
uses — calling the existing `generate(config, paths, edition_id)` per edition (which already
generates every declared language for that edition when `--language` is omitted). Each resulting
`GeneratedDocument.pdf_path` is copied into `dist_dir / f"{edition_id}-{language}.pdf"`.

**Rationale**: `ProjectConfig.list_editions()` and `generate()`'s existing "all languages when
`language=None`" behavior already do exactly what's needed — no new discovery mechanism, no
hardcoded edition/language list anywhere (FR-002/SC-005), and reusing `generate()` means the
release build goes through the identical, already-tested code path as every other invocation
(same content resolution, same template, same watermark/logo pre-flight check).

**Alternatives considered**:
- *A hardcoded edition/language matrix in the workflow YAML*: explicitly rejected by FR-002 — would
  need a pipeline change every time an edition/language is added, defeating SC-005.
- *Parsing `project.yaml` directly in the workflow with a YAML tool (`yq`)*: rejected — would
  duplicate `ProjectConfig`'s validation/parsing logic in a second place (and a second language),
  when the exact same information is already one Python call away.

## 3. How is a release/hotfix branch's version validated against `pyproject.toml`?

**Decision**: A new `src/wh40k_cheatsheet/versioning.py` module: `parse_release_branch(branch)`
strips a `release/` or `hotfix/` prefix (returning `None` for any other branch name, e.g.
`feature/x`, `develop`, `main` — those simply have nothing to validate); `is_valid_semver(version)`
matches the canonical SemVer 2.0.0 regex (below); `is_prerelease(version)` reports whether a
pre-release component is present. The `validate-version` CLI command chains these: parse the branch
name argument, validate the extracted version is well-formed SemVer, read `pyproject.toml`'s
`[project].version` via the stdlib `tomllib`, and raise `VersionError` (joining `KNOWN_ERRORS`,
same pattern as every other pipeline error) if either check fails — printing both values in the
error message per the spec's edge case ("naming both values").

```text
^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)
(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$
```

This is the official regex published at semver.org for SemVer 2.0.0, unmodified.

**Rationale**: Reusing the canonical, widely-reviewed SemVer regex avoids inventing (and getting
subtly wrong) pre-release/build-metadata parsing rules. `tomllib` (Python 3.11+ stdlib, already the
project's minimum version) reads `pyproject.toml` without adding a dependency — `pydantic`/`pyyaml`
are already used for `project.yaml`, but `pyproject.toml` is TOML, not YAML, and there's no existing
TOML reader in the project's dependencies.

**Alternatives considered**:
- *A third-party SemVer library (e.g. `python-semver`)*: rejected — a ~20-line stdlib regex fully
  covers this feature's needs (parse + compare-equal + prerelease-detect); a new dependency isn't
  justified for that.
- *Comparing versions as an ordering (`>` the last release) rather than exact match to
  `pyproject.toml`*: out of scope per spec.md's Assumptions — this feature only validates
  well-formedness and branch/file agreement, not monotonic increase.

## 4. How does the workflow ensure publishing only happens after quality + build succeed, from `main`, exactly once, idempotently?

**Decision**: A single workflow file with GitHub Actions' native `needs:` job-dependency graph,
rather than a second workflow chained via `workflow_run`:

- `check` (existing, unchanged): quality gate, all branches.
- `validate-version`: only runs when `github.head_ref || github.ref_name` starts with `release/` or
  `hotfix/`.
- `build`: all branches; `needs: validate-version` **only** when applicable (via `if:`), so a
  version failure prevents any build on those branches (FR-004's "build no PDFs"); uploads
  `dist/*.pdf` as a workflow artifact only when the ref is `release/**`, `hotfix/**`, or `main`.
- `publish-release`: `if: github.ref == 'refs/heads/main'`, `needs: [check, build]` — GitHub
  Actions skips a job whenever any of its `needs:` didn't succeed, which is exactly FR-009's
  requirement with no extra logic. Downloads the *same* artifact `build` already produced (no
  rebuild), reads `pyproject.toml`'s version, and either `gh release create` (tag doesn't exist yet)
  or `gh release upload --clobber` (tag exists — updates assets in place, satisfying FR-011) with
  `--prerelease` set based on `is_prerelease`.

**Rationale**: A single-workflow, multi-job design keeps the "only publish after success" guarantee
structural (the job dependency graph itself), rather than relying on a second workflow correctly
re-deriving success/failure from a `workflow_run` event — which has well-documented sharp edges
(the triggering workflow's *default-branch* definition is what runs, event payloads differ
subtly from the originating push). Downloading the already-built artifact instead of rebuilding on
`main` also directly serves the spirit of FR-009: the release being published is provably the exact
build that already passed quality+build, not a fresh, potentially-different one.

**Alternatives considered**:
- *`workflow_run` chaining a separate `release.yml`*: rejected for the fragility above.
- *Rebuilding from scratch in `publish-release` instead of downloading the artifact*: rejected —
  redundant work, and a (however unlikely) non-determinism between the two builds would undermine
  "publish exactly what already passed."

## 5. How is the GitHub Release itself created/updated, and what does "no third-party Action" mean concretely?

**Decision**: The `gh` CLI, pre-installed on every GitHub-hosted runner, authenticated via the
default `GITHUB_TOKEN` (job-scoped `permissions: contents: write`):

```bash
if gh release view "$TAG" >/dev/null 2>&1; then
  gh release upload "$TAG" dist/*.pdf --clobber
else
  gh release create "$TAG" dist/*.pdf --title "$TAG" --target "$GITHUB_SHA" \
    $( [ "$IS_PRERELEASE" = "true" ] && echo --prerelease )
fi
```

**Rationale**: `gh` is official GitHub tooling, already present with zero setup on the runner image
used — no marketplace Action (and its own supply-chain/version-pinning surface) is needed for
something the pre-installed CLI already does directly, matching the constitution's "a new runtime
dependency MUST be justified" for CI tooling too.

**Alternatives considered**:
- *`softprops/action-gh-release` (a popular third-party Action)*: rejected — capable, but an
  unnecessary third-party dependency when `gh release create`/`gh release upload --clobber` covers
  the exact same create-or-update behavior (FR-011) with tooling already on the runner.
- *GitHub's REST API directly via `curl`*: rejected — `gh` already wraps this correctly (pagination,
  multipart asset upload, auth) with far less code to get right.

## 6. How should CI auto-bump `pyproject.toml`/`uv.lock` on a release/hotfix push? (2026-09-14 amendment)

**Decision**: Keep the release/hotfix branch name as the sole source of the target version — no
GitVersion-style inference from commit history or message content. On a direct push (never a pull
request), extend the existing `validate-version` command with a `--fix` flag: on a mismatch, it
rewrites `pyproject.toml`'s `[project].version` via a new `write_project_version` function (plain
text substitution, no new dependency — `pyproject.toml`'s version is always a single-line string
assignment in this project), the workflow then runs `uv lock` (only if that changed something) and
commits + pushes both files back to the branch with `git`, tools already present on the runner.

**Rationale**: This is the minimal change that removes the one remaining manual step (hand-editing
two files before every release push) without introducing a second versioning policy alongside the
branch-name convention FR-003 already establishes. `uv.lock` needs its own re-lock because it
embeds this project's own package version (`source = { editable = "." }` entries record it) —
skipping that step would leave `uv sync --locked` failing on the very next CI step once
`pyproject.toml` no longer matches the lock file.

**Alternatives considered**:
- *Infer the version bump from conventional-commit messages (real GitVersion/semantic-release
  behavior)*: rejected as explicitly out of scope by the 2026-09-14 clarification — adds a second,
  less predictable source of truth for "what version is this," and nothing in this project's commit
  history follows a conventional-commit format today, so it would need to be adopted as a new
  process convention first.
- *A TOML-writing library (`tomlkit`) for a fully round-trip-safe edit*: rejected — a scoped,
  line-anchored text substitution (research.md's existing minimalism precedent, §1/§5) already
  preserves every other byte of the file for the one shape `pyproject.toml`'s version line
  actually takes here; a new dependency buys nothing observable.
- *Compute and use the bumped version only in-memory for that CI run, never committing it back*:
  rejected per the 2026-09-14 clarification — leaves the checked-in `pyproject.toml`/`uv.lock`
  permanently one version behind what actually shipped, which is exactly the drift `validate-version`
  originally existed to catch.
- *Also bump `main` to a new dev/prerelease version right after a release/hotfix merge*: rejected
  per the 2026-09-14 clarification — `main` only ever reflects a shipped version; starting the next
  cycle's version bump is deferred to whenever the next release/hotfix branch is cut, unchanged from
  today.
