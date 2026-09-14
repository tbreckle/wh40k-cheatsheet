# Contract: CI/CD Workflow Job Graph

Feature: [spec.md](../spec.md) · Plan: [plan.md](../plan.md) · Data model: [data-model.md](../data-model.md)

**Amendment 2026-09-14**: `validate-version` (J2) now branches by event type — a pull request
still only verifies (unchanged from before this amendment); a direct push auto-fixes, re-locks,
and commits/pushes instead (FR-013). `publish-prerelease` (J5) additionally checks out the
branch's current tip rather than the triggering commit, so it observes that auto-fix commit. See
J2's and J5's updated rows and the mechanism snippet below.

---

## Trigger contract

| # | Guarantee | Basis |
|---|-----------|-------|
| T1 | The workflow runs on `push` to `feature/**`, `develop`, `release/**`, `hotfix/**`, and `main` | FR-001; FR-002 |
| T2 | The workflow also runs on `pull_request` targeting `develop` or `main` | FR-001 (GitFlow's PR targets) |

## Job contract

| # | Guarantee | Basis |
|---|-----------|-------|
| J1 | `check` (existing, unchanged): runs `uv run poe check` on every triggering event | FR-001 |
| J2 | `validate-version`: runs only when the ref (`github.head_ref \|\| github.ref_name`) starts with `release/` or `hotfix/`. On a `pull_request` event, runs `uv run wh40k-cheatsheet validate-version <head_ref>` unchanged (verify-only). On a `push` event (2026-09-14 amendment), instead runs `uv run wh40k-cheatsheet validate-version <ref_name> --fix`, then `uv lock` if `pyproject.toml` changed, then commits + pushes `pyproject.toml`/`uv.lock` back to that branch if either changed — never both branches of behavior in the same run, since `pull_request` and `push` are mutually exclusive event types | FR-003; FR-004; FR-013 |
| J3 | `build`: runs on every triggering event; runs `uv run wh40k-cheatsheet package`; `needs: validate-version` **only** when the ref is `release/**`/`hotfix/**` (so a version failure — or, on `push`, a failed auto-fix — prevents any build on those branches, per FR-004's "build no PDFs") | FR-002; FR-004; FR-013 |
| J4 | `build` uploads `dist/*.pdf` as a workflow artifact named `cheatsheet-pdfs` **only** when the ref is `release/**`, `hotfix/**`, or `main` (feature/develop pushes don't need it) | FR-005; contracts/cli-package-command.md |
| J5 | `publish-prerelease`: runs **only** for a `push` event (never a `pull_request`) whose `github.ref_name` starts with `release/` or `hotfix/`; `needs: [check, build]`; checks out `ref: ${{ github.ref_name }}` rather than the default triggering SHA (2026-09-14 amendment), so `read_project_version` below sees J2's auto-fix commit rather than a stale pre-fix version | FR-006; FR-009; FR-012; FR-013 |
| J6 | `publish-release`: runs **only** when `github.ref == 'refs/heads/main'` AND `needs.check.result`/`needs.build.result` are both `'success'` (2026-09-14 bug fix — see P9 and "Known boundaries" below for why this must be checked explicitly rather than via bare `success()`); `needs: [check, build]` | FR-007; FR-009; FR-010; FR-012 |
| J7 | Both `publish-prerelease` and `publish-release` download the `cheatsheet-pdfs` artifact produced by `build` in the *same run* — neither ever rebuilds | research.md §4 |

## Publish contract

| # | Guarantee | Basis |
|---|-----------|-------|
| P1 | The release tag is `v<pyproject.toml version>` (read fresh in the publishing job) | FR-006; FR-007 |
| P2 | Every downloaded PDF is attached as a release asset, filenames unchanged (`<edition_id>-<language>.pdf`) | FR-006; FR-007; FR-008 |
| P3 | If `gh release view "$TAG"` succeeds (release already exists), assets are updated via `gh release upload "$TAG" dist/*.pdf --clobber`; otherwise a new release is created via `gh release create` | FR-011 |
| P4 | `publish-prerelease` always passes `--prerelease` (create) / `gh release edit --prerelease` (update) — regardless of whether the version string itself has a pre-release component | FR-006 |
| P5 | `publish-release` passes `--prerelease` (create) or `gh release edit --target "$GITHUB_SHA" --prerelease[=false]` (update, explicitly promoting a pre-existing pre-release) based on `is_prerelease(version)` | FR-010 |
| P6 | `publish-prerelease` never runs for a `pull_request` event or for `main` — structurally, via the job's `if:`, not a runtime check that could be bypassed; `publish-release` never runs for a ref other than `refs/heads/main` | FR-012 |
| P7 | The job's `permissions:` are scoped to `contents: write` only on `publish-prerelease`, `publish-release`, and (2026-09-14 amendment) `validate-version` — the minimum needed for each to push a commit/tag; `check` and `build` keep the default read-only token | Least-privilege; constitution's security posture |
| P8 (2026-09-14) | `validate-version`'s auto-fix commit (J2) always includes `[skip ci]` in its message, so the push it makes does not itself trigger a second, redundant workflow run — the branch's version is corrected exactly once per genuine push | Avoids doubling CI cost per release-branch push; no FR directly requires this, it is a cost/consistency choice |
| P9 (2026-09-14 bug fix) | `publish-prerelease` and `publish-release` gate on `needs.check.result == 'success' && needs.build.result == 'success'`, never bare `success()` | FR-009; see "Known boundaries" below |

## Mechanism (implementation detail, documented for traceability)

```yaml
on:
  push:
    branches: ["feature/**", "develop", "release/**", "hotfix/**", "main"]
  pull_request:
    branches: [develop, main]

jobs:
  check:
    # unchanged from today's quality.yml

  validate-version:
    # 2026-09-14 amendment: PRs still only verify; pushes auto-fix, re-lock, and push the fix.
    if: startsWith(github.head_ref || github.ref_name, 'release/') || startsWith(github.head_ref || github.ref_name, 'hotfix/')
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --locked
      - if: github.event_name == 'pull_request'
        run: uv run wh40k-cheatsheet validate-version "${{ github.head_ref }}"
      - if: github.event_name == 'push'
        run: uv run wh40k-cheatsheet validate-version "${{ github.ref_name }}" --fix
      - if: github.event_name == 'push'
        run: git diff --quiet -- pyproject.toml || uv lock
      - if: github.event_name == 'push'
        run: |
          if ! git diff --quiet -- pyproject.toml uv.lock; then
            git config user.name "github-actions[bot]"
            git config user.email "github-actions[bot]@users.noreply.github.com"
            git add pyproject.toml uv.lock
            git commit -m "chore: bump version to ${GITHUB_REF_NAME#*/} [skip ci]"
            git push origin "HEAD:${GITHUB_REF_NAME}"
          fi

  build:
    needs: ${{ (startsWith(github.head_ref || github.ref_name, 'release/') || startsWith(github.head_ref || github.ref_name, 'hotfix/')) && 'validate-version' || '' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # ... native deps + uv sync, same as `check` ...
      - run: uv run wh40k-cheatsheet package
      - if: startsWith(github.ref_name, 'release/') || startsWith(github.ref_name, 'hotfix/') || github.ref_name == 'main'
        uses: actions/upload-artifact@v4
        with:
          name: cheatsheet-pdfs
          path: dist/*.pdf

  publish-prerelease:
    if: needs.check.result == 'success' && needs.build.result == 'success' && github.event_name == 'push' && (startsWith(github.ref_name, 'release/') || startsWith(github.ref_name, 'hotfix/'))
    needs: [check, build]
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.ref_name }} # 2026-09-14: picks up validate-version's auto-fix commit
      - uses: actions/download-artifact@v4
        with: { name: cheatsheet-pdfs, path: dist }
      - id: version
        run: echo "version=$(uv run python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")" >> "$GITHUB_OUTPUT"
      - env:
          GH_TOKEN: ${{ github.token }}
          TAG: v${{ steps.version.outputs.version }}
        run: |
          if gh release view "$TAG" >/dev/null 2>&1; then
            gh release upload "$TAG" dist/*.pdf --clobber
            gh release edit "$TAG" --target "$GITHUB_SHA" --prerelease
          else
            gh release create "$TAG" dist/*.pdf --title "$TAG" --target "$GITHUB_SHA" --prerelease
          fi

  publish-release:
    if: needs.check.result == 'success' && needs.build.result == 'success' && github.ref == 'refs/heads/main'
    needs: [check, build]
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/download-artifact@v4
        with: { name: cheatsheet-pdfs, path: dist }
      - id: version
        run: echo "version=$(uv run python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")" >> "$GITHUB_OUTPUT"
      - env:
          GH_TOKEN: ${{ github.token }}
          TAG: v${{ steps.version.outputs.version }}
          PRERELEASE: ${{ steps.version.outputs.prerelease }}
        run: |
          PRERELEASE_FLAG="--prerelease=false"
          [ "$PRERELEASE" = "true" ] && PRERELEASE_FLAG="--prerelease"
          if gh release view "$TAG" >/dev/null 2>&1; then
            gh release upload "$TAG" dist/*.pdf --clobber
            gh release edit "$TAG" --target "$GITHUB_SHA" $PRERELEASE_FLAG
          else
            gh release create "$TAG" dist/*.pdf --title "$TAG" --target "$GITHUB_SHA" $PRERELEASE_FLAG
          fi
```

Note: the `needs:` expression in `build` above is illustrative — GitHub Actions doesn't support a
conditional `needs:` value directly; the equivalent is expressed with `if:` on `build` checking
`needs.validate-version.result` combined with an always-present-but-conditionally-skipped
`validate-version` job (GitHub Actions' documented pattern for optional prerequisites). The exact
YAML is a `tasks.md`/implementation-time detail; this contract fixes the *behavior* (J2/J3), not the
literal expression syntax.

## Known boundaries

- **Bare `success()` is unsafe whenever a job's dependency chain contains an *intentionally*
  skipped job further upstream, even one not in that job's own `needs:` list** (2026-09-14 bug
  fix, reported against a real `main`-branch run: `check` and `build` both succeeded, but
  `publish-release` stayed skipped anyway). `success()` in a job's `if:` evaluates across that
  job's *entire transitive* dependency chain, not just its direct `needs:`. `publish-release`'s
  `needs: [check, build]` doesn't list `validate-version` at all — but `build` itself needs
  `validate-version`, which is *always* skipped on `main` by design (T1/J2 — `main` never matches
  the `release/`/`hotfix/` prefix check). `success()` sees that non-`success` conclusion somewhere
  in the ancestry and returns `false`, unconditionally, on every push to `main`. The fix (P9): gate
  on `needs.check.result == 'success' && needs.build.result == 'success'` instead — this only
  inspects the two jobs actually named in `needs:`, so `validate-version`'s skip (three hops away
  from `publish-release`, two from `publish-prerelease`) never enters into it. Before this fix,
  `publish-release` could never run at all, since a push to `main` always skips
  `validate-version` — this made User Story 1 (the feature's core deliverable) entirely
  non-functional despite every individual job passing.
- General takeaway for any *future* job added to this graph with its own `needs:` and a
  hand-written `if:`: prefer explicit `needs.<job>.result == 'success'` checks for each name
  actually listed in that job's own `needs:` over bare `success()`/`failure()`, whenever any job
  reachable through that `needs:` chain (directly or transitively) is ever conditionally skipped
  by design — which, in this workflow, `validate-version` is, on every branch that isn't
  `release/*`/`hotfix/*`.
