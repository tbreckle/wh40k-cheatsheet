# Contract: `validate-version` CLI Command

Feature: [spec.md](../spec.md) · Plan: [plan.md](../plan.md) · Data model: [data-model.md](../data-model.md)

**Amendment 2026-09-14**: adds an optional `--fix` flag (FR-013) that corrects a version mismatch
by rewriting `pyproject.toml` instead of failing. Every other guarantee below (G1–G4, F1) is
unchanged and applies identically whether or not `--fix` is passed.

---

## CLI contract

| # | Guarantee | Basis |
|---|-----------|-------|
| G1 | `wh40k-cheatsheet validate-version <branch>` is a no-op success (exit `0`) for any branch name that isn't `release/*` or `hotfix/*`, with or without `--fix` | data-model.md §3 step 1 — safe to run unconditionally |
| G2 | For a `release/X.Y.Z` or `hotfix/X.Y.Z` branch, the command validates `X.Y.Z` is well-formed SemVer 2.0.0 (research.md §3's regex), failing loudly (non-zero exit, `VersionError`, clear message) if not — `--fix` does not suppress this failure, since there is no valid value it could write | FR-003; FR-004; Edge case: malformed version |
| G3 | Without `--fix`, the command then validates `X.Y.Z` exactly equals `pyproject.toml`'s `[project].version` (relative to `--project-root`), failing loudly and naming *both* values if they disagree | FR-004; Edge case: "a clear error naming both values" |
| G4 | On success, the command prints to stdout and exits `0`: the version string alone when it already matched, or `"<old> -> <new>"` when `--fix` corrected a mismatch | data-model.md §3 step 5 |
| G5 (2026-09-14) | With `--fix`, a mismatch is corrected by calling `write_project_version` (rewriting only `pyproject.toml`'s `[project].version` line, per contracts/cli-validate-version-command.md's sibling `versioning.write_project_version` behavior) instead of raising `VersionError`; when the version already matches, `--fix` has no effect (no write, same output as without the flag) | FR-013 |

## Example

```bash
$ uv run wh40k-cheatsheet validate-version release/1.2.0
1.2.0

$ uv run wh40k-cheatsheet validate-version feature/foo
feature/foo: not a release/hotfix branch, nothing to validate

$ uv run wh40k-cheatsheet validate-version release/1.2
Error: 'release/1.2' does not contain a valid SemVer version: '1.2'
$ echo $?
1

$ uv run wh40k-cheatsheet validate-version release/1.3.0   # pyproject.toml says 1.2.0
Error: branch 'release/1.3.0' declares version '1.3.0', but pyproject.toml declares '1.2.0'
$ echo $?
1

$ uv run wh40k-cheatsheet validate-version release/1.3.0 --fix   # pyproject.toml said 1.2.0
1.2.0 -> 1.3.0
$ echo $?
0
```

## Failure-mode contract

| # | Guarantee | Basis |
|---|-----------|-------|
| F1 | `VersionError` joins `cli.py`'s `KNOWN_ERRORS` tuple — reported via the same `logger.critical` + exit-`1` path as every other pipeline error, not an uncaught traceback | Consistency with existing CLI error handling |
