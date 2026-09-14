# Development

## Setup

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

WeasyPrint needs native libraries installed on the host: Pango, cairo, GDK-PixBuf, HarfBuzz
(installed automatically in CI; install via your OS package manager locally).

## Quality gates

All tool configuration lives in `pyproject.toml` (no per-tool dotfiles). One command runs every
gate — format check, lint (ruff + pylint), security (bandit), types (ty), tests (pytest):

```bash
uv run poe check
```

Full local run currently completes in ~7s on this codebase (well under the 30s budget).

Individual gates: `uv run poe format-check`, `poe lint`, `poe security`, `poe types`, `poe test`.
Auto-fix the mechanical subset: `uv run poe fix`.

Enforced rule set (see `pyproject.toml` `[tool.ruff.lint]` / `[tool.pylint]`): pycodestyle,
pyflakes, isort, pep8-naming, pyupgrade, bugbear, comprehensions, simplify, pathlib, bandit subset,
pylint parity, perflint, refurb, and more — line length is **120 characters** everywhere.

A finding may be suppressed for one line only, with a reason: `# noqa: <rule>  # reason: ...`
(ruff), `# pylint: disable=<check>` with an adjacent comment, or `# nosec <id>` (bandit). Blanket or
unexplained suppressions are rejected in review; ruff's `RUF100` flags unused `noqa` comments.

Every module, class, function, and method in `src/wh40k_cheatsheet` — public and private alike —
requires a [Google-style docstring](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
(`tests/` is exempt). Enforced by ruff's `D`/pydocstyle rules (presence + formatting, public scope)
and pylint's docstring checks plus its `docparams` extension (presence across public + private
scope, and that `Args:`/`Returns:`/`Raises:` actually match the signature) — both fail `poe lint`
the same way an existing lint/type/security finding does. Full contract:
`specs/008-google-style-docstrings/contracts/docstring-style.md`.

CI (`.github/workflows/quality.yml`) runs the identical `uv run poe check` on every push/PR across
every GitFlow branch (see "Continuous Integration" below); mark the `check` job as a required
status check so failing gates block merge.

## Continuous Integration

`.github/workflows/quality.yml` follows [GitFlow](https://nvie.com/posts/a-successful-git-branching-model/):
`feature/*` branches integrate into `develop`; `release/*`/`hotfix/*` branches integrate into
`main`. Every push/PR gets the quality gate and a full build of every declared edition/language,
downloadable as a workflow artifact; only a merge into `main` ever publishes a GitHub Release.

| Branch pattern | `check` (quality gate) | `validate-version` | `build` (`package`) | Artifact uploaded | `publish-release` |
|---|---|---|---|---|---|
| `feature/**` | ✅ | — | ✅ | **Yes** | Never |
| `develop` | ✅ | — | ✅ | **Yes** | Never |
| `release/**` (push) | ✅ | ✅ auto-bumps + commits, gates `build` | ✅ (only if version valid) | **Yes** | Never |
| `hotfix/**` (push) | ✅ | ✅ auto-bumps + commits, gates `build` | ✅ (only if version valid) | **Yes** | Never |
| `release/**`/`hotfix/**` (PR into develop/main) | ✅ | ✅ verify-only, gates `build` | ✅ (only if version valid) | **Yes** | Never |
| `main` | ✅ | — | ✅ | **Yes** | ✅ (`needs: [check, build]`) |

A `release/*`/`hotfix/*` branch's name encodes its target SemVer version (e.g. `release/1.2.0`).
Full contract: `specs/012-gitflow-release-pipeline/contracts/ci-workflow.md`.

## Versioning & releases

The project's version lives in `pyproject.toml`'s `[project].version` and follows
[SemVer 2.0.0](https://semver.org/). To cut a release, push a branch named `release/X.Y.Z` (or
`hotfix/X.Y.Z`) — that's the only manual step. On every push to that branch, CI itself rewrites
`pyproject.toml`'s version to `X.Y.Z`, re-runs `uv lock` so `uv.lock` stays in sync, and commits +
pushes both back to the branch (2026-09-14 amendment) — you never hand-edit either file. A pull
request from that branch into `develop`/`main` only re-verifies the two already agree, as a safety
net. Two CLI commands back this:

```bash
uv run wh40k-cheatsheet package                                # build every edition/language into dist/
uv run wh40k-cheatsheet validate-version release/1.2.0          # verify a release/hotfix branch's version
uv run wh40k-cheatsheet validate-version release/1.2.0 --fix    # ...or rewrite pyproject.toml to match it
```

`package` stages every declared edition/language as `dist/<edition_id>-<language>.pdf`, flat —
what CI attaches to a GitHub Release. `validate-version` is a no-op on any branch that isn't
`release/*`/`hotfix/*`; with `--fix`, a version mismatch is corrected instead of failing the
command (a malformed branch version still fails either way). Merging a `release/*`/`hotfix/*`
branch into `main` publishes (or updates) a GitHub Release tagged `v<version>`, marked as a
pre-release if the version has a pre-release component (e.g. `1.3.0-rc.1`). Full contracts:
`specs/012-gitflow-release-pipeline/contracts/cli-package-command.md` and
`specs/012-gitflow-release-pipeline/contracts/cli-validate-version-command.md`.

## Reproducibility

WeasyPrint does not embed a wall-clock timestamp, so regenerating the same (edition, revision,
language) from unchanged sources produces byte-identical PDF output.
