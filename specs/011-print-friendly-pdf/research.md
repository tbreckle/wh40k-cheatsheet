# Phase 0 Research: Print-Friendly PDF Flag

No `[NEEDS CLARIFICATION]` markers remained in the Technical Context after drafting it — this
feature reuses the existing Jinja2/WeasyPrint stack unchanged, so no new technology needed
evaluation. The open questions were design decisions, resolved below.

## 1. How to produce a grayscale rendering without a new dependency

**Decision**: Add a single CSS block, scoped to `body.print-friendly`, that redeclares every
existing color custom property (`--green-dark`, `--green-sub`, `--ink`, `--cream`, `--info-bg`,
`--your-bg`, `--opp-bg`, `--either-bg`, `--rule`, etc.) with a grayscale hex value. CSS custom
properties inherit down the DOM, so overriding them once on `<body>` — toggled by a Jinja
conditional class driven by a new `document.print_friendly` context flag — recolors every element
that already consumes `var(--x)`, with zero changes to any rule that isn't color-related (spacing,
borders' widths, `break-inside`, etc. are untouched).

**Rationale**: The entire existing color system already flows through custom properties declared
once in `:root` (confirmed by inspection of `templates/cheatsheet.html.j2`) — there are no
hard-coded colors on individual rules except a handful of one-off values (`#fff`, `rgba(255,255,255,.18)`,
`#f2f4ef` zebra-stripe, `#2f6ba3` info icon) that also need grayscale equivalents but are just as
easily overridden by a handful of additional selector-scoped rules alongside the variable block.
This keeps the entire feature declarative and co-located with the palette it's overriding, with no
duplication of the template's structural CSS or markup.

**Alternatives considered**:
- *Duplicate the whole `<style>` block/template for a "print" variant*: rejected — doubles the
  surface that must stay in sync on every future template change (a new block type, a new
  color-bearing rule) and directly invites drift; the constitution's Code Quality principle
  explicitly calls for factoring shared logic rather than copying it.
- *Post-process the rendered PDF into grayscale (e.g. via Pillow/pikepdf rasterization)*: rejected
  — WeasyPrint output is vector-and-text, not raster; converting to grayscale this way would mean
  rasterizing crisp text into images (or adding a new PDF-manipulation dependency), which the
  constitution requires justifying against the cost of adding it. A CSS-only approach needs no new
  dependency and keeps text as real, selectable/searchable text in the output PDF.
- *A `filter: grayscale(1)` CSS filter on the whole document*: rejected — WeasyPrint's supported
  CSS subset does not implement CSS Filter Effects, and even where filters are supported elsewhere,
  a computed desaturation doesn't guarantee the specific tonal separation needed to keep the four
  stratagem-timing variants distinguishable (FR-005); explicit grey values give direct control.

**Implementation-time amendment**: the original decision text above described overriding these
custom properties via a `body.print-friendly` class selector. During implementation this was found
to be insufficient: the running header/footer is CSS Paged Media `@page` margin-box content
(`@top-center`, `@bottom-left`, `@bottom-right`), which consumes `var(--green-dark)`/`var(--muted)`
but inherits custom properties from the page context, not from `<body>` — a body-scoped override
silently fails to recolor it. The values are instead resolved once per property directly in the
`:root` block via a server-side Jinja conditional on `print_friendly` (each print-friendly document
is already a wholly separate render pass, so this is no more complex than the class-based approach
and is correct regardless of how a given engine implements paged-media custom-property
inheritance). See data-model.md §2 and contracts/print-friendly-flag.md for the shipped mechanism.

## 2. How to omit (not just hide) the background watermark

**Decision**: Wrap the existing `<img class="page-watermark" ...>` tag in a Jinja
`{% if not (document.print_friendly | default(false)) %}...{% endif %}` conditional, so the
print-friendly rendering's HTML never contains an `<img>` reference to `logo_40k.png` at all.

**Rationale**: The spec (FR-003) says the watermark image itself must not be included, not merely
invisible — matching this literally (element absent from the DOM) is both the more literal and the
cheaper choice: `display: none`/`opacity: 0` would still ask WeasyPrint to load and decode the
image for a page that shows nothing, and a test asserting "the watermark box is absent from the
page tree" (the same box-tree technique `test_page_logo_pdf.py` already uses to assert presence)
is simpler than asserting a specific style value. This conditional matches the existing pattern
already used for `list.single_column` and `glossary.spanning` — presence/absence and class
toggling driven by a boolean context flag, evaluated once per block/element.

**Alternatives considered**:
- *CSS-only hide (`display: none` under `.print-friendly`)*: rejected per above — technically
  satisfies "not visible" but not "MUST NOT include...the background watermark image" as literally
  as omitting the element, and needlessly asks WeasyPrint to resolve the asset.

## 3. Where the second render/write pass belongs

**Decision**: `pipeline._generate_one()` performs the standard render/write exactly as it does
today, then — only when a new `print_friendly: bool` parameter is `True` — renders a second time
with a context whose `document` mapping has `print_friendly: True` merged in, and writes that
HTML/PDF pair to sibling files (`{language}-print.html`, `{language}-print.pdf`) in the same
`out_dir`.

**Rationale**: `_generate_one` already owns exactly one render-then-write cycle per document; making
the print-friendly pass conditional and colocated there (rather than a separate pipeline function)
keeps the one-document-in, one-or-two-files-out relationship visible in a single place, and reuses
`render_html`/`render_pdf` unchanged — no new rendering code path, only a second call.

**Alternatives considered**:
- *A wholly separate `generate_print_friendly()` pipeline function*: rejected — would duplicate the
  revision/edition/language resolution and content-loading logic already in `generate()`/`_generate_one()`
  for no benefit, since the print-friendly document is 1:1 with an already-resolved standard one.
- *A separate CLI subcommand (e.g. `generate-print`)*: rejected — the spec explicitly frames this
  as a flag on `generate` (FR-001), and a document's standard and print-friendly forms are always
  generated together in one invocation per FR-007, so a single flag reads more naturally than a
  second subcommand a user must remember to also invoke.

## 4. Output file naming

**Decision**: `{language}-print.html` / `{language}-print.pdf`, sibling files to the existing
`{language}.html` / `{language}.pdf` in the same `out_root/edition_id/revision_id/` directory.

**Rationale**: Matches the project's existing flat, per-language file-per-directory layout (no new
subdirectory, no new path-construction logic beyond a suffix); immediately visually adjacent to its
standard counterpart when listing the output directory; consistent with how the CLI already reports
one line per generated file, extended to two lines per document when the flag is set (FR-009).

**Alternatives considered**:
- *A `print/` subdirectory mirroring the standard layout*: rejected — adds a second directory tree
  to create/maintain for no material benefit over a filename suffix, and department from every
  other per-document artifact in the project, which lives flat in its revision directory.

## 5. Preserving non-color distinction between callout/stratagem variants (FR-005)

**Decision**: Rely primarily on content that already exists — the stratagem timing bar's icon +
text label (`▶ YOUR TURN`, `◀ OPPONENT'S TURN`, `◆ EITHER PLAYER'S TURN`) and the callout icon
(`⚠` vs `ℹ`) — and reinforce it with distinct grey shades per variant in the new palette (e.g.
lightest grey for "your turn", a mid grey for "opponent", a third for "either"/"info"), rather than
collapsing all variants to one identical grey.

**Rationale**: Inspection of `templates/cheatsheet.html.j2` shows every color-only distinction in
the document already has a redundant non-color signal (icon and/or text) — this was already true
before this feature, so satisfying FR-005 requires no new markup, only choosing grey values that
don't happen to collide, verified by the WCAG-aligned contrast check in Constitution Principle III.

**Alternatives considered**:
- *Border-style variation (solid/dashed/dotted) as the primary distinguishing signal*: not needed
  as the primary mechanism given the pre-existing icon/text redundancy, but kept as an option in
  data-model.md's palette notes if a future review finds two grey shades too close in practice.
