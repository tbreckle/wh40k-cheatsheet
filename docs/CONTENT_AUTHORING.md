# Content authoring & CLI reference

## Generating cheat sheets

```bash
uv run wh40k-cheatsheet list
uv run wh40k-cheatsheet generate --edition 11e                      # all languages, latest revision
uv run wh40k-cheatsheet generate --edition 11e --language en        # one language, latest revision
uv run wh40k-cheatsheet generate --edition 11e --revision 2026-06-01-00 --language de
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

## Project configuration (`project.yaml`)

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

## Editions, revisions, and content

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
stratagem cards, glossary, etc.) and `editions/11e/2026-06-01-00/{en,de}/content.yaml` for a
complete worked example (English and German).

For a heading nested one level below a `phase` — e.g. a named step within a phase — use
`{type: subphase}`:

```yaml
document:
  blocks:
    - type: phase
      title: "1. COMMAND PHASE"
    - type: subphase
      title: "1a. Battle-shock Step"
```

It carries a `title` like a normal `phase` heading and reuses its typography/padding — the only
difference is a slightly brighter background color, which is what makes it visually distinguishable
as a heading nested inside a `phase` without needing a different width or shape. Full contract:
`specs/014-subphase-block/contracts/subphase-block.md`.

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

A `{type: glossary}` block's `terms` always render in alphabetical order by `term`, regardless of
the order they're written in `content.yaml` — you don't need to keep entries sorted by hand when
authoring or translating. Accented characters sort under their base letter (German `Ä`/`Ö`/`Ü` sort
with `A`/`O`/`U`, `ß` with `ss`), matching that language's dictionary order. A term written with a
leading `[` (e.g. `[ANTI-X Y+] (24.03)`, used for weapon-ability keywords) sorts as if that `[` were
absent — under its first letter, not clustered before every other term. Ordering never affects an
entry's `text`/`html` content, only its position. Full contract:
`specs/013-glossary-alphabetical-sort/contracts/glossary-term-ordering.md`.

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

### Translating the template's own labels (`document.i18n`)

Some text on the sheet comes from the template rather than from authored blocks: the page footer and
the stratagem card's timing banner and body labels. Translate them with an optional `document.i18n`
map:

```yaml
document:
  language: "de"
  i18n:
    page: "Seite"                         # footer: "Seite 1 / 3"
    timing_your: "DEIN ZUG"               # stratagem timing banner
    timing_opponent: "ZUG DES GEGNERS"
    timing_either: "ZUG BEIDER SPIELER"
    label_when: "WANN"                    # stratagem body labels
    label_target: "ZIEL"
    label_effect: "EFFEKT"
    label_restrictions: "EINSCHRÄNKUNGEN"
```

Every key is optional and falls back to its English default (`Page`, `YOUR TURN`, `OPPONENT'S TURN`,
`EITHER PLAYER'S TURN`, `WHEN`, `TARGET`, `EFFECT`, `RESTRICTIONS`), so an English `content.yaml` can
omit `i18n` entirely and a translation can supply only the keys it needs. Write the `label_*` values
**without** the trailing colon — the template adds it.

## Page logo watermark

Every generated page shows the Warhammer 40,000 logo (`images/logo_40k.png`) as a large, faint
(5% opacity) background watermark, rotated 45° and scaled as large as possible while staying fully
visible within the page bounds. This is **not** an authored content-block flag — it is unconditional,
sits strictly behind all other content (never obscuring it), and appears identically on every page
regardless of content or language. Generation fails loudly with a clear error if the logo file is
missing (rather than silently shipping a PDF without it, which is what WeasyPrint would otherwise
do). Full contract: `specs/010-page-header-logo/contracts/page-logo.md`.

## Print-friendly output

Passing `--print-friendly` to `generate` produces an additional PDF (and its retained HTML) that
renders every color in black, white, or grey and omits the background logo watermark entirely —
suited to black-and-white printing. It's written alongside the standard output, never replacing
it: `out/<edition-id>/<revision-id>/<lang-code>-print.{html,pdf}` next to the existing
`<lang-code>.{html,pdf}`. Text content, section structure, and page/column breaks are identical to
the standard PDF; the four callout/stratagem-timing variants stay distinguishable from one another
via their existing icon/text labels, reinforced by distinct grey shades. Omitting the flag leaves
`generate`'s output completely unchanged. Full contract:
`specs/011-print-friendly-pdf/contracts/print-friendly-flag.md`.
