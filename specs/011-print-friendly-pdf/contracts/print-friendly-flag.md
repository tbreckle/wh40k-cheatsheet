# Contract: Print-Friendly PDF Flag

Feature: [spec.md](../spec.md) · Plan: [plan.md](../plan.md) · Data model: [data-model.md](../data-model.md)

---

## CLI contract

| # | Guarantee | Basis |
|---|-----------|-------|
| C1 | `generate` accepts a new `--print-friendly` flag (boolean, `action="store_true"`, default `False`) | FR-001 |
| C2 | `--print-friendly` composes with `--edition`, `--revision`, and `--language` exactly like any other `generate` flag — no ordering constraint, no mutual exclusion | FR-001, FR-004 |
| C3 | Omitting `--print-friendly` leaves `generate`'s behavior, output files, and printed result lines byte-for-byte identical to before this feature | FR-008; SC-004 |
| C4 | When `--print-friendly` is passed, `generate` prints one additional result line per generated document, naming the print-friendly PDF's path, alongside the existing standard-PDF line | FR-009 |

## Render contract

| # | Guarantee | Basis |
|---|-----------|-------|
| G1 | Every element that would otherwise render in color (phase/subsection headers, table header row and zebra stripe, callout backgrounds/borders/icons, stratagem card header and timing bars) instead renders using only black, white, or a shade of grey (R == G == B in the computed style) | FR-002; SC-001; data-model.md §2 |
| G2 | The background logo watermark `<img>` element is absent from the rendered document entirely — not merely hidden — on every page | FR-003; SC-002; research.md §2 |
| G3 | Text content, section structure, and page/column break placement are identical between the print-friendly and standard renderings of the same (edition, revision, language) | FR-004; SC-003 |
| G4 | The three stratagem-timing variants ("your turn", "opponent's turn", "either") and the two callout variants ("warn", "info") remain visually distinguishable from one another without relying on color — via their existing icon/text labels, reinforced by distinct grey shades per variant | FR-005; SC-005; data-model.md §2; research.md §5 |
| G5 | The print-friendly rendering is driven solely by `document.print_friendly` (`bool`, default `false`) in the Jinja render context — no other context shape change | data-model.md §1 |

## Output-file contract

| # | Guarantee | Basis |
|---|-----------|-------|
| O1 | When `print_friendly=True` is requested, both the standard PDF/HTML and the print-friendly PDF/HTML are written for each resolved (edition, revision, language) — the print-friendly output is additional, never a replacement | FR-006, FR-007; SC-004 |
| O2 | The print-friendly PDF/HTML are written to `{out_dir}/{language}-print.pdf` / `{out_dir}/{language}-print.html`, siblings of the standard `{out_dir}/{language}.pdf` / `{out_dir}/{language}.html` in the same directory — neither pair ever overwrites the other | FR-006; data-model.md §3 |
| O3 | `GeneratedDocument.print_pdf_path`/`print_html_path` are `None` unless `print_friendly=True` was requested for that `generate()` call | data-model.md §3 |

---

## CSS mechanism (implementation detail, documented for traceability)

Resolved at `:root` via a server-side Jinja conditional, not a `body.print-friendly` class
override — `@page` margin-box content (the running header/footer) inherits custom properties from
the page context, not from `<body>`, so a body-scoped override would silently miss it (discovered
during implementation; see data-model.md §2's implementation note):

```jinja
{%- set print_friendly = document.print_friendly | default(false) if document is defined else false -%}
...
:root {
  --green-dark: {{ '#262626' if print_friendly else '#1e4d34' }};
  --green-sub: {{ '#595959' if print_friendly else '#5f8a6e' }};
  --green-line: {{ '#333333' if print_friendly else '#24513a' }};
  --ink: {{ '#111111' if print_friendly else '#17170f' }};
  --muted: {{ '#444444' if print_friendly else '#444' }};
  --cream: {{ '#f2f2f2' if print_friendly else '#f6f1d8' }};
  --cream-brd: {{ '#999999' if print_friendly else '#cdbf7a' }};
  --info-bg: {{ '#e0e0e0' if print_friendly else '#e6eef6' }};
  --info-brd: {{ '#888888' if print_friendly else '#a9c3dc' }};
  --your-bg: {{ '#ffffff' if print_friendly else '#dcefe1' }};
  --your-ink: {{ '#000000' if print_friendly else '#1f6b3d' }};
  --opp-bg: {{ '#cccccc' if print_friendly else '#f7e0e0' }};
  --opp-ink: {{ '#000000' if print_friendly else '#9c3030' }};
  --either-bg: {{ '#e6e6e6' if print_friendly else '#f6ecc8' }};
  --either-ink: {{ '#000000' if print_friendly else '#8a6d16' }};
  --rule: {{ '#999999' if print_friendly else '#b9bfb0' }};
}
{%- if print_friendly %}
.callout--info .callout__icon { color: #333333; }
table.data tbody tr:nth-child(even) td { background: #f0f0f0; }
{%- endif %}
```

```html
<body class="{{ 'print-friendly' if print_friendly else '' }}">
  {%- if not print_friendly %}
  <img class="page-watermark" src="../images/logo_40k.png" alt="">
  {%- endif %}
  ...
```

The `print-friendly` body class is retained for self-documentation, but no CSS rule depends on it
— the two non-variable overrides above are gated directly by the same server-side `print_friendly`
flag, since both live in normal body content, not a `@page` margin box.

## Pipeline mechanism (implementation detail, documented for traceability)

```python
def generate(config, paths, edition_id, revision=None, language=None, *, print_friendly=False):
    ...
    return [
        _generate_one(config, paths, edition_id, resolved_revision, lang, print_friendly=print_friendly)
        for lang in languages
    ]

def _generate_one(config, paths, edition_id, revision, language, *, print_friendly=False):
    context = resolve_content(...)
    html = render_html(paths.templates_root, template_name, context, stage_context=stage_context)
    # ... write html_path / pdf_path as today ...

    print_html_path = print_pdf_path = None
    if print_friendly:
        print_context = {**context, "document": {**context["document"], "print_friendly": True}}
        print_html = render_html(paths.templates_root, template_name, print_context, stage_context=stage_context)
        print_html_path = out_dir / f"{language}-print.html"
        print_pdf_path = out_dir / f"{language}-print.pdf"
        print_html_path.write_text(print_html, encoding="utf-8")
        render_pdf(print_html, base_url=paths.templates_root, output_path=print_pdf_path, stage_context=stage_context)

    return GeneratedDocument(..., print_html_path=print_html_path, print_pdf_path=print_pdf_path)
```
