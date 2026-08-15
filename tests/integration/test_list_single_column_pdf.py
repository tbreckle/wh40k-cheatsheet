from pathlib import Path

import weasyprint

from wh40k_cheatsheet.render.html_renderer import render_html

TEMPLATES_ROOT = Path(__file__).resolve().parents[2] / "templates"


def _document(blocks: list[dict]) -> dict:
    return {"document": {"title": "Test", "language": "en", "blocks": blocks}}


def _paragraph(text: str) -> dict:
    return {"type": "paragraph", "text": text}


def _list(items: list, *, single_column: bool | None = None) -> dict:
    block = {"type": "list", "items": items}
    if single_column is not None:
        block["single_column"] = single_column
    return block


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


def test_single_column_list_box_width_approximates_full_content_width():
    html = _render(
        [
            _paragraph("filler"),
            _list(["SPANMARKER item"], single_column=True),
        ]
    )
    standard_width = _find_block_width(html, "filler", "p")
    full_width = _find_block_width(html, "SPANMARKER", "ul")
    # A standard block confined to one column is roughly half the page's content width;
    # the full-width list's box should be close to double that.
    assert full_width > standard_width * 1.5


def test_standard_list_stays_confined_to_one_column():
    html = _render([_list(["STANDARDMARKER item"])])
    filler_width = _find_block_width(html, "STANDARDMARKER", "ul")
    # No flag set at all (omitted, not just false) — must match pre-feature behavior exactly.
    assert '<div class="block block--full-width">' not in html
    assert '<div class="block">' in html
    assert filler_width < 500  # well under a full A4 content width


def test_content_before_and_after_full_width_list_is_preserved():
    html = _render(
        [
            _paragraph("BEFORECONTENT"),
            _list(["SPANMARKER item"], single_column=True),
            _paragraph("AFTERCONTENT"),
        ]
    )
    assert "BEFORECONTENT" in html
    assert "AFTERCONTENT" in html
    assert html.index("BEFORECONTENT") < html.index("SPANMARKER") < html.index("AFTERCONTENT")


def test_full_width_list_nested_sub_items_render_correctly():
    html = _render(
        [
            _list(
                [{"text": "PARENTITEM", "sub": ["SUBITEMONE", "SUBITEMTWO"]}],
                single_column=True,
            )
        ]
    )
    assert "PARENTITEM" in html
    assert "SUBITEMONE" in html
    assert "SUBITEMTWO" in html
    assert html.index("PARENTITEM") < html.index("SUBITEMONE") < html.index("SUBITEMTWO")
    assert '<ul class="sub">' in html


def test_full_width_list_coexists_with_page_break_and_column_reset():
    html = _render(
        [
            _paragraph("One"),
            _page_break(),
            _paragraph("two-a"),
            _list(["SPANMARKER item"], single_column=True),
            _paragraph("two-b"),
            _column_reset(),
            _paragraph("Three"),
        ]
    )
    without_span = _render(
        [
            _paragraph("One"),
            _page_break(),
            _paragraph("two-a"),
            _list(["standard item"]),
            _paragraph("two-b"),
            _column_reset(),
            _paragraph("Three"),
        ]
    )
    # page_break forces exactly one extra page; column_reset (with room remaining) doesn't;
    # the full-width list doesn't participate in segmentation, so page counts match.
    assert _page_count(html) == _page_count(without_span)
    span_width = _find_block_width(html, "SPANMARKER", "ul")
    filler_width = _find_block_width(html, "two-a", "p")
    assert span_width > filler_width * 1.5


def test_full_width_list_at_document_start_renders_correctly():
    html = _render([_list(["STARTMARKER item"], single_column=True), _paragraph("after")])
    width = _find_block_width(html, "STARTMARKER", "ul")
    filler_width = _find_block_width(html, "after", "p")
    assert width > filler_width * 1.5


def test_full_width_list_at_document_end_renders_correctly():
    html = _render([_paragraph("before"), _list(["ENDMARKER item"], single_column=True)])
    width = _find_block_width(html, "ENDMARKER", "ul")
    filler_width = _find_block_width(html, "before", "p")
    assert width > filler_width * 1.5
