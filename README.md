# wh40k-cheatsheet

Generates a templated, multi-language, multi-edition Warhammer 40,000 cheat sheet PDF from
YAML content via a Jinja2 → HTML → WeasyPrint pipeline, with revision (dated correction) support.

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
`main`. Every push/PR gets the quality gate and a full build of every declared edition/language;
only a merge into `main` ever publishes a GitHub Release.

| Branch pattern | `check` (quality gate) | `validate-version` | `build` (`package`) | Artifact uploaded | `publish-release` |
|---|---|---|---|---|---|
| `feature/**` | ✅ | — | ✅ | No | Never |
| `develop` | ✅ | — | ✅ | No | Never |
| `release/**` | ✅ | ✅ gates `build` | ✅ (only if version valid) | **Yes** | Never |
| `hotfix/**` | ✅ | ✅ gates `build` | ✅ (only if version valid) | **Yes** | Never |
| `main` | ✅ | — | ✅ | **Yes** | ✅ (`needs: [check, build]`) |

A `release/*`/`hotfix/*` branch's name encodes its target SemVer version (e.g. `release/1.2.0`),
which is validated against `pyproject.toml`'s version before anything is built on that branch. Full
contract: `specs/012-gitflow-release-pipeline/contracts/ci-workflow.md`.

## Generating cheat sheets

```bash
uv run wh40k-cheatsheet list
uv run wh40k-cheatsheet generate --edition 11e                      # all languages, latest revision
uv run wh40k-cheatsheet generate --edition 11e --language en        # one language, latest revision
uv run wh40k-cheatsheet generate --edition 11e --revision 2026-08-01-00 --language de
uv run wh40k-cheatsheet generate --edition 11e --language en --print-friendly  # + grayscale PDF
```

Output is written to `out/<edition-id>/<revision-id>/<lang-code>.{html,pdf}` — the HTML is a
retained, inspectable intermediate; the PDF is the final artifact. A single (edition, language) PDF
currently generates in ~6s (well under the 10s budget).

### Progress logging & verbose mode

By default, `generate` prints one `INFO` line per major stage (config loaded, revision resolved,
content resolved, template rendered, PDF converted) to **stderr**, while the existing result output
(`generate`'s success lines, `list`'s output) stays on **stdout**, unchanged:

```bash
uv run wh40k-cheatsheet generate --edition 11e --language en
```

Pass `-v`/`--verbose` — before or after the subcommand — to add `DEBUG`-level diagnostic detail
(resolved paths, chosen template/revision) on top of the default `INFO` lines. Verbosity never
changes the generated `.html`/`.pdf` bytes:

```bash
uv run wh40k-cheatsheet -v generate --edition 11e --language en
uv run wh40k-cheatsheet generate --edition 11e --language en --verbose   # same effect
```

| Level | Used for | Emitted at default? | Emitted with `--verbose`? |
|-------|----------|:---:|:---:|
| `DEBUG` | Diagnostic detail: resolved paths, chosen template/revision | No | Yes |
| `INFO` | Per-stage status | Yes | Yes |
| `WARNING` | Reserved for future non-fatal anomalies; no current emitter | Yes, if emitted | Yes, if emitted |
| `CRITICAL` | Run-terminating failures | **Always** | **Always** |

`ERROR` is deliberately not used — every failure this CLI raises is run-terminating, so it is logged
at `CRITICAL` instead, which is always emitted regardless of the verbosity threshold. Full contract:
`specs/004-cli-logging/contracts/logging-contract.md`.

### Project configuration (`project.yaml`)

A single, structure-only YAML file declares every edition, its default template, and its supported
languages (with optional per-language template overrides):

```yaml
editions:
  11e:
    template: cheatsheet.html.j2
    languages:
      en: {}
      de:
        template: cheatsheet.de.html.j2   # optional override
```

Full schema/validation rules: `specs/002-pdf-generation/contracts/config-schema.md`.

### Editions, revisions, and content

Revisions are **not** declared in `project.yaml` — they are discovered from the filesystem layout:

```text
editions/<edition-id>/<revision-id>/<lang-code>/content.yaml
```

`<revision-id>` is `YYYY-MM-DD-NN` (a real calendar date + a two-digit daily sequence `00`–`99`,
i.e. up to 100 revisions per day). `generate` uses the **latest** revision of an edition unless
`--revision` is given explicitly. `list` shows every edition's revisions in chronological order with
the latest marked.

`content.yaml` provides the render context consumed by `templates/*.html.j2` — see
`templates/cheatsheet.html.j2` for the supported content-block vocabulary (phases, callouts, tables,
stratagem cards, glossary, etc.) and `editions/11e/2026-08-01-00/{en,de}/content.yaml` for a
complete worked example (English and German).

To force a new page at a specific point, insert `{type: page_break}` between two blocks:

```yaml
document:
  blocks:
    - type: phase
      title: "..."
    - type: page_break     # everything after this starts on a new page
    - type: phase
      title: "..."
```

No other fields are read from a `page_break` block; a marker at the very start/end of the document,
or several in a row, never produce a blank page. Full contract:
`specs/005-page-breaks/contracts/page-break-block.md`.

To realign to a left column **without** forcing a new page, insert `{type: column_reset}`:

```yaml
document:
  blocks:
    - type: subsection
      title: "..."
    - type: column_reset     # everything after this starts in a left column — same page if room
    - type: subsection
      title: "..."
```

Unlike `page_break`, a `column_reset` only starts a new page when the current one genuinely has no
room left (it naturally overflows there, same as any other content) — otherwise it stays on the same
page. If a `page_break` and a `column_reset` are adjacent with nothing between them, `page_break`
always wins (forces the page), regardless of order. Full contract:
`specs/006-column-reset/contracts/column-reset-block.md`.

For a heading whose text and background span the **full width of both columns** — a clear visual
break, rather than a heading confined to a single column — use `{type: spanning_headline}`:

```yaml
document:
  blocks:
    - type: subsection
      title: "..."
    - type: spanning_headline
      title: "NEW MAJOR SECTION"
    - type: subsection
      title: "..."
```

It carries a `title` like a normal `phase` heading and reuses its color/typography — the only
difference is that it spans both columns instead of being confined to one, which is what makes it
visually distinguishable. It coexists freely with `page_break` and `column_reset`. Full contract:
`specs/007-spanning-headline/contracts/spanning-headline-block.md`.

An existing `{type: glossary}` block can opt into the same full-width treatment for its title bar
only, by adding `spanning: true`:

```yaml
document:
  blocks:
    - type: glossary
      title: "CORE ABILITIES"
      spanning: true          # optional; defaults to off
      terms:
        - {term: "ASSAULT", text: "..."}
```

Both the title bar and the term list span the full width when enabled — the term *content* itself is
unaffected either way. Omitting the flag (or setting it to `false`) renders exactly as before this
addition. Full contract:
`specs/007-spanning-headline/contracts/glossary-spanning-flag.md`.

A `{type: list}` block can opt into the same full-width treatment, by adding `single_column: true`:

```yaml
document:
  blocks:
    - type: list
      single_column: true    # optional; defaults to off
      items:
        - "A long item that reads better across the full page width"
```

The list spans the complete two-column width instead of being confined to one. Omitting the flag
(or setting it to `false`) renders exactly as before this feature. Full contract:
`specs/009-list-single-column/contracts/list-single-column-flag.md`.

### Page logo watermark

Every generated page shows the Warhammer 40,000 logo (`images/logo_40k.png`) as a large, faint
(5% opacity) background watermark, rotated 45° and scaled as large as possible while staying fully
visible within the page bounds. This is **not** an authored content-block flag — it is unconditional,
sits strictly behind all other content (never obscuring it), and appears identically on every page
regardless of content or language. Generation fails loudly with a clear error if the logo file is
missing (rather than silently shipping a PDF without it, which is what WeasyPrint would otherwise
do). Full contract: `specs/010-page-header-logo/contracts/page-logo.md`.

### Print-friendly output

Passing `--print-friendly` to `generate` produces an additional PDF (and its retained HTML) that
renders every color in black, white, or grey and omits the background logo watermark entirely —
suited to black-and-white printing. It's written alongside the standard output, never replacing
it: `out/<edition-id>/<revision-id>/<lang-code>-print.{html,pdf}` next to the existing
`<lang-code>.{html,pdf}`. Text content, section structure, and page/column breaks are identical to
the standard PDF; the four callout/stratagem-timing variants stay distinguishable from one another
via their existing icon/text labels, reinforced by distinct grey shades. Omitting the flag leaves
`generate`'s output completely unchanged. Full contract:
`specs/011-print-friendly-pdf/contracts/print-friendly-flag.md`.

### Reproducibility

WeasyPrint does not embed a wall-clock timestamp, so regenerating the same (edition, revision,
language) from unchanged sources produces byte-identical PDF output.

### Versioning & releases

The project's version lives in `pyproject.toml`'s `[project].version` and follows
[SemVer 2.0.0](https://semver.org/). To cut a release, bump that version, then push a branch named
`release/X.Y.Z` (or `hotfix/X.Y.Z`) with the identical version — CI validates the two agree before
building anything. Two CLI commands back this:

```bash
uv run wh40k-cheatsheet package                          # build every edition/language into dist/
uv run wh40k-cheatsheet validate-version release/1.2.0    # validate a release/hotfix branch's version
```

`package` stages every declared edition/language as `dist/<edition_id>-<language>.pdf`, flat —
what CI attaches to a GitHub Release. `validate-version` is a no-op on any branch that isn't
`release/*`/`hotfix/*`. Merging a `release/*`/`hotfix/*` branch into `main` publishes (or updates)
a GitHub Release tagged `v<version>`, marked as a pre-release if the version has a pre-release
component (e.g. `1.3.0-rc.1`). Full contracts:
`specs/012-gitflow-release-pipeline/contracts/cli-package-command.md` and
`specs/012-gitflow-release-pipeline/contracts/cli-validate-version-command.md`.

## Acknowledgements

The 11th edition content in `editions/11e/2026-08-01-00/en/content.yaml` is transcribed from a
community-made cheat sheet shared on Reddit — thank you to its original creator:
<https://www.reddit.com/r/Warhammer40k/comments/1tv312v/11th_edition_cheat_sheet/>. The
translations are a derivative work of that content.
