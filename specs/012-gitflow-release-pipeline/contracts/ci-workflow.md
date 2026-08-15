# Contract: CI/CD Workflow Job Graph

Feature: [spec.md](../spec.md) · Plan: [plan.md](../plan.md) · Data model: [data-model.md](../data-model.md)

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
| J2 | `validate-version`: runs only when the ref (`github.head_ref \|\| github.ref_name`) starts with `release/` or `hotfix/`; runs `uv run wh40k-cheatsheet validate-version <ref>` | FR-003; FR-004 |
| J3 | `build`: runs on every triggering event; runs `uv run wh40k-cheatsheet package`; `needs: validate-version` **only** when the ref is `release/**`/`hotfix/**` (so a version failure prevents any build on those branches, per FR-004's "build no PDFs") | FR-002; FR-004 |
| J4 | `build` uploads `dist/*.pdf` as a workflow artifact named `cheatsheet-pdfs` **only** when the ref is `release/**`, `hotfix/**`, or `main` (feature/develop pushes don't need it) | FR-005; contracts/cli-package-command.md |
| J5 | `publish-release`: runs **only** when `github.ref == 'refs/heads/main'`; `needs: [check, build]` — GitHub Actions skips this job automatically if either needed job failed | FR-006; FR-007; FR-009; FR-010; FR-012 |
| J6 | `publish-release` downloads the `cheatsheet-pdfs` artifact produced by `build` in the *same run* — it never rebuilds | research.md §4 |

## Publish contract

| # | Guarantee | Basis |
|---|-----------|-------|
| P1 | The release tag is `v<pyproject.toml version>` (read fresh in the `publish-release` job) | FR-007 |
| P2 | Every downloaded PDF is attached as a release asset, filenames unchanged (`<edition_id>-<language>.pdf`) | FR-007; FR-008 |
| P3 | If `gh release view "$TAG"` succeeds (release already exists), assets are updated via `gh release upload "$TAG" dist/*.pdf --clobber`; otherwise a new release is created via `gh release create` | FR-011 |
| P4 | `gh release create` passes `--prerelease` iff the version contains a pre-release component (`is_prerelease`) | FR-010 |
| P5 | `publish-release` never runs for a ref other than `refs/heads/main` — structurally, via the job's `if:`, not a runtime check that could be bypassed | FR-006; FR-012 |
| P6 | The job's `permissions:` are scoped to `contents: write` only on `publish-release`; every other job keeps the default read-only token | Least-privilege; constitution's security posture |

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
    if: startsWith(github.head_ref || github.ref_name, 'release/') || startsWith(github.head_ref || github.ref_name, 'hotfix/')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --locked
      - run: uv run wh40k-cheatsheet validate-version "${{ github.head_ref || github.ref_name }}"

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

  publish-release:
    if: github.ref == 'refs/heads/main'
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
        run: |
          if gh release view "$TAG" >/dev/null 2>&1; then
            gh release upload "$TAG" dist/*.pdf --clobber
          else
            PRERELEASE_FLAG=""
            case "$TAG" in *-*) PRERELEASE_FLAG="--prerelease" ;; esac
            gh release create "$TAG" dist/*.pdf --title "$TAG" --target "$GITHUB_SHA" $PRERELEASE_FLAG
          fi
```

Note: the `needs:` expression in `build` above is illustrative — GitHub Actions doesn't support a
conditional `needs:` value directly; the equivalent is expressed with `if:` on `build` checking
`needs.validate-version.result` combined with an always-present-but-conditionally-skipped
`validate-version` job (GitHub Actions' documented pattern for optional prerequisites). The exact
YAML is a `tasks.md`/implementation-time detail; this contract fixes the *behavior* (J2/J3), not the
literal expression syntax.
