from pathlib import Path

import weasyprint

from wh40k_cheatsheet.render.html_renderer import render_html

TEMPLATES_ROOT = Path(__file__).resolve().parents[2] / "templates"


def _document(blocks: list[dict]) -> dict:
    return {"document": {"title": "Test", "language": "en", "blocks": blocks}}


def _phase(title: str) -> dict:
    return {"type": "phase", "title": title}


def _spanning(title: str) -> dict:
    return {"type": "spanning_headline", "title": title}


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


def _find_block_width(html: str, marker_text: str, tag: str) -> float:
    doc = weasyprint.HTML(string=html, base_url=str(TEMPLATES_ROOT)).render()
    for page in doc.pages:
        found = _search_block_by_tag(page._page_box, marker_text, tag)
        if found is not None:
            return found
    raise AssertionError(f"<{tag}> containing '{marker_text}' not found in any page")


def _search_block_by_tag(box, marker_text: str, tag: str) -> float | None:
    element = getattr(box, "element", None)
    if getattr(element, "tag", None) == tag and _contains_text(box, marker_text):
        return box.width
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


def test_spanning_headline_box_width_approximates_full_content_width():
    html = _render([_paragraph("filler"), _spanning("SPANNINGMARKER")])
    standard_width = _find_block_width(html, "filler", "p")
    spanning_width = _find_block_width(html, "SPANNINGMARKER", "h2")
    # A standard block confined to one column is roughly half the page's content width;
    # the spanning headline's box should be close to double that.
    assert spanning_width > standard_width * 1.5


def test_spanning_headline_wider_than_standard_phase_heading():
    html = _render([_phase("STANDARDMARKER"), _spanning("SPANNINGMARKER")])
    standard_width = _find_block_width(html, "STANDARDMARKER", "h2")
    spanning_width = _find_block_width(html, "SPANNINGMARKER", "h2")
    assert spanning_width > standard_width * 1.5


def test_multiple_spanning_headlines_each_render_independently():
    html = _render(
        [
            _paragraph("a"),
            _spanning("FIRSTSPAN"),
            _paragraph("b"),
            _spanning("SECONDSPAN"),
            _paragraph("c"),
        ]
    )
    first_width = _find_block_width(html, "FIRSTSPAN", "h2")
    second_width = _find_block_width(html, "SECONDSPAN", "h2")
    filler_width = _find_block_width(html, "a", "p")
    assert first_width > filler_width * 1.5
    assert second_width > filler_width * 1.5


def test_spanning_headline_at_document_start_renders_correctly():
    html = _render([_spanning("STARTSPAN"), _paragraph("after")])
    width = _find_block_width(html, "STARTSPAN", "h2")
    filler_width = _find_block_width(html, "after", "p")
    assert width > filler_width * 1.5


def test_spanning_headline_at_document_end_renders_correctly():
    html = _render([_paragraph("before"), _spanning("ENDSPAN")])
    width = _find_block_width(html, "ENDSPAN", "h2")
    filler_width = _find_block_width(html, "before", "p")
    assert width > filler_width * 1.5


def test_content_before_and_after_spanning_headline_is_preserved():
    html = _render([_paragraph("BEFORECONTENT"), _spanning("MID"), _paragraph("AFTERCONTENT")])
    assert "BEFORECONTENT" in html
    assert "AFTERCONTENT" in html
    assert html.index("BEFORECONTENT") < html.index("MID") < html.index("AFTERCONTENT")


def test_spanning_headline_coexists_with_page_break_and_column_reset():
    html = _render(
        [
            _phase("One"),
            _page_break(),
            _paragraph("two-a"),
            _spanning("SPANMARKER"),
            _paragraph("two-b"),
            _column_reset(),
            _phase("Three"),
        ]
    )
    # page_break forces exactly one extra page; column_reset (with room remaining) doesn't.
    without_span = _render(
        [
            _phase("One"),
            _page_break(),
            _paragraph("two-a"),
            _paragraph("two-b"),
            _column_reset(),
            _phase("Three"),
        ]
    )
    assert _page_count(html) == _page_count(without_span)
    span_width = _find_block_width(html, "SPANMARKER", "h2")
    filler_width = _find_block_width(html, "two-a", "p")
    assert span_width > filler_width * 1.5
