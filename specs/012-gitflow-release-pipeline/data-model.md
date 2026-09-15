# Phase 1 Data Model: GitFlow CI/CD Release Pipeline

This feature adds no `content.yaml`/`project.yaml` schema changes. Its "entities" are the CLI's new
inputs/outputs and the CI workflow's job graph, documented below in place of a traditional
entity/relationship model.

## 1. `versioning` module

| Name | Shape | Notes |
|---|---|---|
| `parse_release_branch(branch: str) -> str \| None` | function | Strips a leading `release/` or `hotfix/` prefix and returns the remainder verbatim (not yet validated as SemVer); returns `None` for any branch without one of those prefixes (`feature/x`, `develop`, `main`, etc.) — those branches simply have nothing to validate. |
| `SEMVER_PATTERN` | compiled `re.Pattern` | The canonical SemVer 2.0.0 regex (research.md §3), unmodified from semver.org. |
| `is_valid_semver(version: str) -> bool` | function | `True` iff `version` fully matches `SEMVER_PATTERN`. |
| `is_prerelease(version: str) -> bool` | function | `True` iff `version` matches `SEMVER_PATTERN` **and** its pre-release capture group is non-empty (e.g. `1.3.0-rc.1` → `True`; `1.3.0` and `1.3.0+build5` → `False`). |
| `VersionError(RuntimeError)` | exception | Raised by the `validate-version` CLI command; joins `KNOWN_ERRORS` in `cli.py` so it's reported and exits `1` the same way every other pipeline error already is. |
| `write_project_version(project_root: Path, version: str) -> bool` (2026-09-14) | function | Rewrites `pyproject.toml`'s `[project].version` line in place to `version`, scoped to lines inside the `[project]` table (never touches a same-named key elsewhere); returns `True` if it actually changed the file, `False` if `version` already matched (no write). Raises `VersionError` if the file or its `[project].version` is missing. Used by `validate-version --fix` (§3). |

## 2. `package` CLI command / `package_all` pipeline function

| Field | Type | Notes |
|---|---|---|
| `package_all(config: ProjectConfig, paths: Paths, dist_dir: Path) -> list[Path]` | function | For every `edition_id` in `config.list_editions()` (declaration order — the same source `list_inventory` uses): calls `generate(config, paths, edition_id)` (every declared language for that edition), then for each resulting `GeneratedDocument` copies `pdf_path` to `dist_dir / f"{edition_id}-{language}.pdf"`. Returns the list of staged paths, in generation order. Any failure (a `ContentError`/`RenderError`/`PdfError` from `generate`) propagates immediately — `dist_dir` is left with whatever was staged before the failure, never presented as a complete/successful build (matches the spec's all-or-nothing edge case: the CI step itself fails, so a partial `dist_dir` is never uploaded as an artifact or released). |
| `dist/<edition_id>-<language>.pdf` | output file | One per declared (edition, language) pair. Flat directory — GitHub Release assets and workflow artifacts have no folder structure, so the edition/language identity lives entirely in the filename (FR-008). |

CLI surface: `wh40k-cheatsheet package [--project-root .] [--dist-dir dist]`. No `--edition`/
`--language` filters — deliberately always builds everything declared, matching FR-002's "every
edition and every language declared," not a selectable subset.

## 3. `validate-version` CLI command

CLI surface: `wh40k-cheatsheet validate-version <branch> [--project-root .] [--fix]`.

| Step | Behavior |
|---|---|
| 1. Parse | `parse_release_branch(branch)`. If `None` (not a release/hotfix branch), the command exits `0` immediately printing `"<branch>: not a release/hotfix branch, nothing to validate"` — a no-op success, not an error, so it's safe to run unconditionally on any branch name without special-casing the caller. `--fix` has no effect on this step. |
| 2. Validate format | `is_valid_semver(version)`. If `False`, raise `VersionError` naming the branch and the malformed version — always, `--fix` included, since there is no valid value to write. |
| 3. Read project version | `pyproject.toml`'s `[project].version`, read via `tomllib.load` relative to `--project-root`. |
| 4. Compare | If the branch's version ≠ the project's version: without `--fix`, raise `VersionError` naming both values (spec's edge case: "a clear error naming both values"); with `--fix` (2026-09-14), call `write_project_version` instead, print `"<old> -> <new>"`, and exit `0`. |
| 5. Success (already matching) | Print the validated version to stdout; exit `0`. Identical whether or not `--fix` was passed — there is nothing to fix. |

## 4. GitFlow Branch → CI job behavior matrix

| Branch pattern | `check` (quality gate) | `validate-version` | `build` (`package`) | Build artifact uploaded? | `publish-release` |
|---|---|---|---|---|---|
| `feature/**` | ✅ | — (parses to `None`, no-op) | ✅ | No | Never (not `main`) |
| `develop` | ✅ | — | ✅ | No | Never |
| `release/**` (push) | ✅ | ✅ auto-fixes + commits (2026-09-14), gates `build` | ✅ (only if fix succeeded) | **Yes** | Never (not `main`) |
| `hotfix/**` (push) | ✅ | ✅ auto-fixes + commits (2026-09-14), gates `build` | ✅ (only if fix succeeded) | **Yes** | Never (not `main`) |
| `release/**`/`hotfix/**` (pull request) | ✅ | ✅ verify-only, gates `build` | ✅ (only if version valid) | **Yes** | Never (not `main`) |
| `main` | ✅ | — (parses to `None`, no-op) | ✅ | **Yes** | ✅ (`needs: [check, build]`) |

## 5. GitHub Release

| Field | Value |
|---|---|
| Tag | `v<pyproject.toml version>`, e.g. `v1.2.0` |
| Target commit | The `main`-branch commit that triggered `publish-release` (`$GITHUB_SHA`) |
| Title | Same as the tag, e.g. `v1.2.0` |
| Notes (2026-09-15) | Always rewritten by whichever publish job runs last for the tag: `publish-prerelease` → "Pre-release build from `<branch>` (`<sha>`). Not yet merged into main."; `publish-release` → "Release built from `main` (`<sha>`)." (or a pre-release variant if `is_prerelease(version)`). See contracts/ci-workflow.md P10 |
| Assets | Every file in the downloaded `cheatsheet-pdfs` artifact — one `<edition_id>-<language>.pdf` per declared edition/language |
| Pre-release flag | `True` iff `is_prerelease(version)` |
| Create-vs-update | `gh release view "$TAG"` exit code decides: nonzero (doesn't exist) → `gh release create`; zero (exists) → `gh release upload --clobber` (replaces assets in place, per FR-011) |
