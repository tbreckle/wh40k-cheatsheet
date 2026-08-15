# Phase 1 Data Model: Print-Friendly PDF Flag

This feature adds no persistent data entities (no new `content.yaml` fields, no schema change).
Its "data" is (a) a render-time context flag, (b) a grayscale color mapping applied by CSS, and
(c) a per-document output-file pairing. Each is documented below in place of a traditional
entity/relationship model.

## 1. Render Context Flag

| Field | Type | Default | Notes |
|---|---|---|---|
| `document.print_friendly` | `bool` | `false` | New optional key on the existing `document` render context (see `templates/cheatsheet.html.j2`'s context-shape comment). Absent or `false` renders exactly as before this feature (FR-008). `true` toggles the `print-friendly` class on `<body>` and omits the watermark `<img>` entirely. Not an authored `content.yaml` field — set by the pipeline, never by edition content. |

## 2. Grayscale Palette Mapping

Every existing color-bearing CSS custom property, resolved directly in the `:root` block via a
server-side Jinja conditional on `print_friendly` (values chosen for (a) exact grayscale —
R == G == B — satisfying FR-002/SC-001, and (b) distinguishable tonal steps between the three
stratagem-timing variants and the two callout variants, reinforced by their pre-existing icon/text
labels, satisfying FR-005/SC-005).

**Implementation note**: resolved at `:root` rather than via a `body.print-friendly` class
override, because `@page` margin-box content (the running header/footer, which consumes
`var(--green-dark)`/`var(--muted)`) inherits custom properties from the page context, not from
`<body>` — a body-scoped override would silently fail to recolor the running header/footer. Since
each print-friendly document is already a wholly separate render pass (not a runtime CSS toggle
within one static file), resolving the value once per property server-side is both correct and
simpler than a CSS-only approach.

| Custom property | Standard value | Print-friendly value | Used for |
|---|---|---|---|
| `--green-dark` | `#1e4d34` | `#262626` | Phase headers, table header row, stratagem card header, running page-header text |
| `--green-sub` | `#5f8a6e` | `#595959` | Subsection bars |
| `--green-line` | `#24513a` | `#333333` | Reserved (declared, not currently consumed by a rule) |
| `--ink` | `#17170f` | `#111111` | Body text |
| `--muted` | `#444` | `#444444` | Footer text, sub-list bullet glyphs (already near-grayscale; redeclared for exactness) |
| `--cream` | `#f6f1d8` | `#f2f2f2` | Default/"warn" callout background |
| `--cream-brd` | `#cdbf7a` | `#999999` | Default/"warn" callout border |
| `--info-bg` | `#e6eef6` | `#e0e0e0` | "info" callout background |
| `--info-brd` | `#a9c3dc` | `#888888` | "info" callout border |
| `--your-bg` | `#dcefe1` | `#ffffff` | Stratagem "your turn" timing bar background |
| `--your-ink` | `#1f6b3d` | `#000000` | Stratagem "your turn" timing bar text |
| `--opp-bg` | `#f7e0e0` | `#cccccc` | Stratagem "opponent's turn" timing bar background |
| `--opp-ink` | `#9c3030` | `#000000` | Stratagem "opponent's turn" timing bar text |
| `--either-bg` | `#f6ecc8` | `#e6e6e6` | Stratagem "either player's turn" timing bar background; also the default callout icon color source (`--either-ink`) |
| `--either-ink` | `#8a6d16` | `#000000` | Stratagem "either" timing bar text; default callout icon color |
| `--rule` | `#b9bfb0` | `#999999` | Table cell borders, stratagem timing-bar bottom border |

Two non-variable, hard-coded colors also need a print-friendly override (they don't consume a
custom property today):

| Rule | Standard value | Print-friendly value | Used for |
|---|---|---|---|
| `.callout--info .callout__icon` | `color: #2f6ba3` | `color: #333333` | "info" callout icon color |
| `table.data tbody tr:nth-child(even) td` | `background: #f2f4ef` | `background: #f0f0f0` | Zebra-striped table rows |

Values intentionally left unchanged (already grayscale, no override needed): `#fff` (white text on
dark headers), `rgba(255, 255, 255, .18)` (translucent white stratagem-cost badge — grayscale
regardless of alpha).

## 3. Output File Pairing

| Field | Type | Notes |
|---|---|---|
| `GeneratedDocument.html_path` | `Path` | Unchanged — standard-rendering HTML, always written. |
| `GeneratedDocument.pdf_path` | `Path` | Unchanged — standard-rendering PDF, always written. |
| `GeneratedDocument.print_html_path` | `Path \| None` | New. Set to `{out_dir}/{language}-print.html` only when `print_friendly=True` was requested for this `generate()` call; `None` otherwise. |
| `GeneratedDocument.print_pdf_path` | `Path \| None` | New. Set to `{out_dir}/{language}-print.pdf` only when `print_friendly=True` was requested; `None` otherwise. |

Both pairs live in the same `out_root/{edition_id}/{revision.id}/` directory, keyed by the same
`edition_id`/`revision`/`language` as the standard pair on the same `GeneratedDocument` — there is
one `GeneratedDocument` per (edition, revision, language), optionally carrying both file pairs.
Filesystem shape:

```text
out/{edition_id}/{revision}/
├── {language}.html              # unchanged
├── {language}.pdf                # unchanged
├── {language}-print.html         # new, only when --print-friendly is passed
└── {language}-print.pdf          # new, only when --print-friendly is passed
```
