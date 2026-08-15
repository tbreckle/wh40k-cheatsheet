from pathlib import Path

import weasyprint

from wh40k_cheatsheet.render.html_renderer import render_html

TEMPLATES_ROOT = Path(__file__).resolve().parents[2] / "templates"


def _page_count(html: str) -> int:
    return len(weasyprint.HTML(string=html, base_url=str(TEMPLATES_ROOT)).render().pages)


def _document(blocks: list[dict]) -> dict:
    return {"document": {"title": "Test", "language": "en", "blocks": blocks}}


def _phase(title: str) -> dict:
    return {"type": "phase", "title": title}


def _break() -> dict:
    return {"type": "page_break"}


def test_no_marker_baseline_is_one_page():
    context = _document([_phase("Alpha"), _phase("Beta")])
    html = render_html(TEMPLATES_ROOT, "cheatsheet.html.j2", context)
    assert _page_count(html) == 1


def test_one_marker_produces_exactly_one_extra_page():
    without = _document([_phase("Alpha"), _phase("Beta")])
    with_break = _document([_phase("Alpha"), _break(), _phase("Beta")])

    pages_without = _page_count(render_html(TEMPLATES_ROOT, "cheatsheet.html.j2", without))
    pages_with = _page_count(render_html(TEMPLATES_ROOT, "cheatsheet.html.j2", with_break))

    assert pages_with == pages_without + 1


def test_content_after_marker_is_in_its_own_sheet_segment():
    context = _document([_phase("Alpha"), _break(), _phase("Beta")])
    html = render_html(TEMPLATES_ROOT, "cheatsheet.html.j2", context)

    assert html.count('<div class="sheet">') == 2
    first_sheet, second_sheet = html.split('<div class="sheet">')[1:]
    assert "Alpha" in first_sheet
    assert "Alpha" not in second_sheet
    assert "Beta" in second_sheet


def test_consecutive_markers_produce_single_page_transition():
    single_break = _document([_phase("Alpha"), _break(), _phase("Beta")])
    double_break = _document([_phase("Alpha"), _break(), _break(), _phase("Beta")])

    pages_single = _page_count(render_html(TEMPLATES_ROOT, "cheatsheet.html.j2", single_break))
    pages_double = _page_count(render_html(TEMPLATES_ROOT, "cheatsheet.html.j2", double_break))

    assert pages_double == pages_single


def test_marker_at_start_and_end_produce_no_blank_pages():
    baseline = _document([_phase("Alpha")])
    start = _document([_break(), _phase("Alpha")])
    end = _document([_phase("Alpha"), _break()])

    pages_baseline = _page_count(render_html(TEMPLATES_ROOT, "cheatsheet.html.j2", baseline))
    pages_start = _page_count(render_html(TEMPLATES_ROOT, "cheatsheet.html.j2", start))
    pages_end = _page_count(render_html(TEMPLATES_ROOT, "cheatsheet.html.j2", end))

    assert pages_start == pages_baseline
    assert pages_end == pages_baseline


def test_three_markers_among_four_sections_yield_four_pages():
    context = _document([_phase("One"), _break(), _phase("Two"), _break(), _phase("Three"), _break(), _phase("Four")])
    html = render_html(TEMPLATES_ROOT, "cheatsheet.html.j2", context)
    assert _page_count(html) == 4
