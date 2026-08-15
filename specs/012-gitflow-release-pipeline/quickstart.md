# Quickstart: GitFlow CI/CD Release Pipeline

Validates the feature end-to-end once implemented. See
[contracts/cli-package-command.md](./contracts/cli-package-command.md),
[contracts/cli-validate-version-command.md](./contracts/cli-validate-version-command.md), and
[contracts/ci-workflow.md](./contracts/ci-workflow.md) for the exact guarantees checked below.

## Part 1 — local CLI validation (no GitHub required)

### Prerequisites

```bash
cd /home/tobi/code/wh40k-cheatsheet
uv sync
```

### 1. `package` builds every edition/language, flat and correctly named

```bash
uv run wh40k-cheatsheet package
ls dist/
```

**Expected**: `dist/11e-en.pdf` and `dist/11e-de.pdf` (today's declared edition/languages —
contract G1/G2). Add a second edition or language to `project.yaml` and re-run: the new file
appears with zero code changes (contract G4).

### 2. `package` fails loudly, no partial output, if one edition/language is broken

```bash
# temporarily break one edition/language's content.yaml (invalid YAML or a bad reference)
uv run wh40k-cheatsheet package; echo "exit: $?"
```

**Expected**: non-zero exit, a clear error naming the broken edition/language/revision (contract
G3/F1) — the CI step this maps to would fail the same way, so nothing broken is ever uploaded or
released.

### 3. `validate-version` accepts a matching, well-formed version

```bash
uv run wh40k-cheatsheet validate-version release/0.1.0   # matches pyproject.toml's current version
echo "exit: $?"
```

**Expected**: prints `0.1.0`, exit `0` (contract G2/G3/G4).

### 4. `validate-version` is a no-op on non-release branches

```bash
uv run wh40k-cheatsheet validate-version feature/some-thing
```

**Expected**: a "not a release/hotfix branch" message, exit `0` (contract G1).

### 5. `validate-version` rejects a malformed or mismatched version

```bash
uv run wh40k-cheatsheet validate-version release/not-semver; echo "exit: $?"
uv run wh40k-cheatsheet validate-version release/9.9.9; echo "exit: $?"   # doesn't match pyproject.toml
```

**Expected**: both fail with exit `1` and a clear message (contract G2/G3).

### 6. Run the automated suite

```bash
uv run pytest tests/unit/test_versioning.py tests/integration/test_package_command.py -v
uv run poe check   # full gate — confirms no regression
```

## Part 2 — end-to-end workflow validation (requires a GitHub remote)

This part can only be exercised once the repository is pushed to GitHub with GitFlow branches
(`main`, `develop`) established — it's a manual walkthrough, not something `pytest` runs.

1. Push a `feature/x` branch with a trivial change. **Expected**: the `check` and `build` jobs run;
   no `validate-version` job runs; no artifact is uploaded; nothing is published (contracts T1, J1,
   J3, J5/P5).
2. Set `pyproject.toml`'s version to a new value, e.g. `0.2.0`, and push a `release/0.2.0` branch.
   **Expected**: `check`, `validate-version`, and `build` all run and pass; `dist/*.pdf` is
   available as a downloadable "cheatsheet-pdfs" artifact on that workflow run; the repository's
   Releases page is unchanged (contracts J2, J3, J4).
3. Push a commit to the same `release/0.2.0` branch with a version that no longer matches
   `pyproject.toml` (e.g. edit only the branch's local commit, not the file). **Expected**:
   `validate-version` fails, `build` is skipped (not run), no artifact for that push.
4. Merge `release/0.2.0` into `main`. **Expected**: `check` and `build` run on the merge commit;
   `publish-release` runs after both succeed and publishes a GitHub Release tagged `v0.2.0`,
   containing every edition/language PDF, marked as a full release (no `-` in `0.2.0`) (contracts
   J5, J6, P1–P4).
5. Re-run the `main` workflow for the same commit (or push an empty commit re-triggering it).
   **Expected**: the existing `v0.2.0` release's assets are replaced, not duplicated, and no error
   occurs (contract P3).
6. Repeat steps 2–4 with a `hotfix/0.2.1` branch. **Expected**: identical behavior to a release
   branch (spec's hotfix-scope clarification).
7. Repeat with a pre-release version, e.g. `release/0.3.0-rc.1` (and matching `pyproject.toml`).
   **Expected**: the resulting GitHub Release is marked "Pre-release" (contract P4).
