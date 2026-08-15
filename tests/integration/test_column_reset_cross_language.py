from pathlib import Path

import weasyprint

from wh40k_cheatsheet.render.html_renderer import render_html

TEMPLATES_ROOT = Path(__file__).resolve().parents[2] / "templates"


def _page_count(html: str) -> int:
    return len(weasyprint.HTML(string=html, base_url=str(TEMPLATES_ROOT)).render().pages)


def _document(language: str, blocks: list[dict]) -> dict:
    return {"document": {"title": "Test", "language": language, "blocks": blocks}}


def _phase(title: str) -> dict:
    return {"type": "phase", "title": title}


def _filler(marker: str) -> dict:
    return {"type": "paragraph", "html": f'<div style="height:200mm">{marker}</div>'}


def _column_reset() -> dict:
    return {"type": "column_reset"}


def _render(document: dict) -> str:
    return render_html(TEMPLATES_ROOT, "cheatsheet.html.j2", document)


def test_equivalent_column_reset_placement_yields_equivalent_outcome_across_languages():
    en_without = _document("en", [_phase("Alpha"), _phase("Beta")])
    en_with = _document("en", [_phase("Alpha"), _column_reset(), _phase("Beta")])
    de_without = _document("de", [_phase("Erste"), _phase("Zweite")])
    de_with = _document("de", [_phase("Erste"), _column_reset(), _phase("Zweite")])

    en_delta = _page_count(_render(en_with)) - _page_count(_render(en_without))
    de_delta = _page_count(_render(de_with)) - _page_count(_render(de_without))

    assert en_delta == 0  # room remains; no page wasted, in either language
    assert de_delta == 0
    assert en_delta == de_delta


def test_equivalent_column_reset_overflow_outcome_across_languages():
    en_fillers = [_filler(f"F{i}") for i in range(6)]
    de_fillers = [_filler(f"G{i}") for i in range(6)]

    en_without = _document("en", [*en_fillers, _phase("Beta")])
    en_with = _document("en", [*en_fillers, _column_reset(), _phase("Beta")])
    de_without = _document("de", [*de_fillers, _phase("Zweite")])
    de_with = _document("de", [*de_fillers, _column_reset(), _phase("Zweite")])

    en_delta = _page_count(_render(en_with)) - _page_count(_render(en_without))
    de_delta = _page_count(_render(de_with)) - _page_count(_render(de_without))

    assert en_delta == de_delta
