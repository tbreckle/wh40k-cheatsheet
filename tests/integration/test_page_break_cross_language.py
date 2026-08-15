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


def _break() -> dict:
    return {"type": "page_break"}


def test_equivalent_marker_placement_yields_equivalent_page_increase_across_languages():
    en_without = _document("en", [_phase("Alpha"), _phase("Beta")])
    en_with = _document("en", [_phase("Alpha"), _break(), _phase("Beta")])
    de_without = _document("de", [_phase("Erste"), _phase("Zweite")])
    de_with = _document("de", [_phase("Erste"), _break(), _phase("Zweite")])

    en_delta = _page_count(render_html(TEMPLATES_ROOT, "cheatsheet.html.j2", en_with)) - _page_count(
        render_html(TEMPLATES_ROOT, "cheatsheet.html.j2", en_without)
    )
    de_delta = _page_count(render_html(TEMPLATES_ROOT, "cheatsheet.html.j2", de_with)) - _page_count(
        render_html(TEMPLATES_ROOT, "cheatsheet.html.j2", de_without)
    )

    assert en_delta == 1
    assert de_delta == 1
    assert en_delta == de_delta
