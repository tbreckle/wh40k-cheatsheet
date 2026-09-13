from pathlib import Path

import weasyprint

from wh40k_cheatsheet.render.html_renderer import render_html

TEMPLATES_ROOT = Path(__file__).resolve().parents[2] / "templates"


def _document(blocks: list[dict]) -> dict:
    return {"document": {"title": "Test", "language": "en", "blocks": blocks}}


def _phase(title: str) -> dict:
    return {"type": "phase", "title": title}


def _subphase(title: str) -> dict:
    return {"type": "subphase", "title": title}


def _paragraph(text: str) -> dict:
    return {"type": "paragraph", "text": text}


def _page_break() -> dict:
    return {"type": "page_break"}


def _column_reset() -> dict:
    return {"type": "column_reset"}


def _render(blocks: list[dict]) -> str:
    return render_html(TEMPLATES_ROOT, "cheatsheet.html.j2", _document(blocks))


def _page_count(html: str) -> int:
    return len(weasyprint.HTML(string=html, base_url=str(TEMPLATES_ROOT)).render().pages)


def _find_block(html: str, marker_text: str, tag: str):
    doc = weasyprint.HTML(string=html, base_url=str(TEMPLATES_ROOT)).render()
    for page in doc.pages:
        found = _search_block_by_tag(page._page_box, marker_text, tag)
        if found is not None:
            return found
    raise AssertionError(f"<{tag}> containing '{marker_text}' not found in any page")


def _search_block_by_tag(box, marker_text: str, tag: str):
    element = getattr(box, "element", None)
    if getattr(element, "tag", None) == tag and _contains_text(box, marker_text):
        return box
    for child in getattr(box, "children", None) or []:
        found = _search_block_by_tag(child, marker_text, tag)
        if found is not None:
            return found
    return None


def _contains_text(box, marker_text: str) -> bool:
    text = getattr(box, "text", None)
    if text and marker_text.casefold() in text.casefold():
        return True
    return any(_contains_text(child, marker_text) for child in getattr(box, "children", None) or [])


def _luminance(color) -> float:
    r, g, b = color.coordinates
    return r + g + b


def test_subphase_background_is_brighter_than_phase():
    html = _render([_phase("PHASEMARKER"), _subphase("SUBPHASEMARKER")])
    phase_bg = _find_block(html, "PHASEMARKER", "h2").style["background_color"]
    subphase_bg = _find_block(html, "SUBPHASEMARKER", "h2").style["background_color"]
    assert _luminance(subphase_bg) > _luminance(phase_bg)


def test_subphase_same_width_as_standard_phase_heading():
    # Unlike spanning_headline, subphase is distinguished purely by color, not width/position.
    html = _render([_phase("PHASEMARKER"), _subphase("SUBPHASEMARKER")])
    phase_width = _find_block(html, "PHASEMARKER", "h2").width
    subphase_width = _find_block(html, "SUBPHASEMARKER", "h2").width
    assert phase_width == subphase_width


def test_multiple_subphases_each_render_independently():
    html = _render(
        [
            _phase("PHASEMARKER"),
            _subphase("FIRSTSUB"),
            _paragraph("a"),
            _subphase("SECONDSUB"),
            _paragraph("b"),
        ]
    )
    phase_bg = _find_block(html, "PHASEMARKER", "h2").style["background_color"]
    first_bg = _find_block(html, "FIRSTSUB", "h2").style["background_color"]
    second_bg = _find_block(html, "SECONDSUB", "h2").style["background_color"]
    assert _luminance(first_bg) > _luminance(phase_bg)
    assert _luminance(second_bg) > _luminance(phase_bg)


def test_subphase_at_document_start_renders_correctly():
    html = _render([_subphase("STARTSUB"), _paragraph("AFTERCONTENT")])
    assert "STARTSUB" in html
    assert "AFTERCONTENT" in html
    assert html.index("STARTSUB") < html.index("AFTERCONTENT")


def test_subphase_at_document_end_renders_correctly():
    html = _render([_paragraph("BEFORECONTENT"), _subphase("ENDSUB")])
    assert "BEFORECONTENT" in html
    assert "ENDSUB" in html
    assert html.index("BEFORECONTENT") < html.index("ENDSUB")


def test_content_before_and_after_subphase_is_preserved():
    html = _render([_paragraph("BEFORECONTENT"), _subphase("MID"), _paragraph("AFTERCONTENT")])
    assert "BEFORECONTENT" in html
    assert "AFTERCONTENT" in html
    assert html.index("BEFORECONTENT") < html.index("MID") < html.index("AFTERCONTENT")


def test_subphase_coexists_with_page_break_and_column_reset():
    html = _render(
        [
            _phase("One"),
            _page_break(),
            _paragraph("two-a"),
            _subphase("SUBMARKER"),
            _paragraph("two-b"),
            _column_reset(),
            _phase("Three"),
        ]
    )
    without_sub = _render(
        [
            _phase("One"),
            _page_break(),
            _paragraph("two-a"),
            _paragraph("two-b"),
            _column_reset(),
            _phase("Three"),
        ]
    )
    assert _page_count(html) == _page_count(without_sub)
    assert "SUBMARKER" in html
