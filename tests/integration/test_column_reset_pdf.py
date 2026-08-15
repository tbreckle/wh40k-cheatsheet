from pathlib import Path

import weasyprint

from wh40k_cheatsheet.render.html_renderer import render_html

TEMPLATES_ROOT = Path(__file__).resolve().parents[2] / "templates"


def _document(blocks: list[dict]) -> dict:
    return {"document": {"title": "Test", "language": "en", "blocks": blocks}}


def _phase(title: str) -> dict:
    return {"type": "phase", "title": title}


def _filler(marker: str) -> dict:
    return {"type": "paragraph", "html": f'<div style="height:200mm">{marker}</div>'}


def _page_break() -> dict:
    return {"type": "page_break"}


def _column_reset() -> dict:
    return {"type": "column_reset"}


def _page_count(html: str) -> int:
    return len(weasyprint.HTML(string=html, base_url=str(TEMPLATES_ROOT)).render().pages)


def _render(blocks: list[dict]) -> str:
    return render_html(TEMPLATES_ROOT, "cheatsheet.html.j2", _document(blocks))


def _find_text_x(html: str, marker_text: str) -> tuple[int, float]:
    doc = weasyprint.HTML(string=html, base_url=str(TEMPLATES_ROOT)).render()
    for page_index, page in enumerate(doc.pages):
        found = _search_box(page._page_box, marker_text)
        if found is not None:
            return page_index, found
    raise AssertionError(f"'{marker_text}' not found in any page")


def _search_box(box, marker_text: str) -> float | None:
    text = getattr(box, "text", None)
    # Some marker text is rendered via CSS text-transform (e.g. uppercase phase titles),
    # so the box tree's text differs in case from the source string.
    if text and marker_text.casefold() in text.casefold():
        return box.position_x
    for child in getattr(box, "children", None) or []:
        found = _search_box(child, marker_text)
        if found is not None:
            return found
    return None


def test_content_after_reset_lands_in_left_column_same_page():
    html = _render([_phase("Alpha"), _column_reset(), _phase("RESETMARKERTEXT")])
    page_index, x = _find_text_x(html, "RESETMARKERTEXT")
    assert page_index == 0
    assert x < 300  # left half of an A4 page


def test_content_after_reset_lands_in_left_column_after_overflow():
    blocks = [_filler(f"F{i}") for i in range(6)] + [_column_reset(), _phase("RESETMARKERTEXT")]
    html = _render(blocks)
    page_index, x = _find_text_x(html, "RESETMARKERTEXT")
    assert page_index > 0  # overflowed past the filler content
    assert x < 300  # still lands in a left column


def test_reset_regardless_of_which_column_preceding_content_ended_in():
    # Whether the preceding content ends in the left or right column, the reset guarantee holds.
    for filler_count in (0, 1, 2, 3):
        blocks = [_phase(f"Fill{i}") for i in range(filler_count)] + [
            _column_reset(),
            _phase("RESETMARKERTEXT"),
        ]
        html = _render(blocks)
        _, x = _find_text_x(html, "RESETMARKERTEXT")
        assert x < 300


def test_reset_with_room_remaining_wastes_no_page():
    without_marker = _render([_phase("Alpha"), _phase("Beta")])
    with_marker = _render([_phase("Alpha"), _column_reset(), _phase("Beta")])
    assert _page_count(with_marker) == _page_count(without_marker)


def test_reset_after_full_page_overflows_naturally():
    fillers = [_filler(f"F{i}") for i in range(6)]
    without_marker = _render([*fillers, _phase("Beta")])
    with_marker = _render([*fillers, _column_reset(), _phase("Beta")])
    # A column_reset never forces an *extra* page beyond what natural overflow already needs.
    assert _page_count(with_marker) == _page_count(without_marker)


def test_page_break_and_column_reset_used_independently():
    html = _render(
        [
            _phase("One"),
            _page_break(),
            _phase("Two"),
            _column_reset(),
            _phase("Three"),
        ]
    )
    assert _page_count(html) == 2  # page_break forces a page; column_reset doesn't (room remains)
    page_of_three, x = _find_text_x(html, "Three")
    assert page_of_three == 1  # same page as "Two" (forced by page_break, not column_reset)
    assert x < 300
