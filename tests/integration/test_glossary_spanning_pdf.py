import re
from pathlib import Path

import weasyprint

from wh40k_cheatsheet.render.html_renderer import render_html

TEMPLATES_ROOT = Path(__file__).resolve().parents[2] / "templates"

GLOSSARY_DIV_RE = re.compile(r'<div class="glossary[^"]*">.*?</div>', re.DOTALL)


def _document(blocks: list[dict]) -> dict:
    return {"document": {"title": "Test", "language": "en", "blocks": blocks}}


def _paragraph(text: str) -> dict:
    return {"type": "paragraph", "text": text}


def _glossary(title: str, *, spanning: bool | None = None) -> dict:
    block = {
        "type": "glossary",
        "title": title,
        "terms": [{"term": "ASSAULT", "text": "Charge into melee."}, {"term": "TORRENT", "text": "Auto-hits."}],
    }
    if spanning is not None:
        block["spanning"] = spanning
    return block


def _render(blocks: list[dict]) -> str:
    return render_html(TEMPLATES_ROOT, "cheatsheet.html.j2", _document(blocks))


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


def _find_glossary_div_width(html: str) -> float:
    doc = weasyprint.HTML(string=html, base_url=str(TEMPLATES_ROOT)).render()
    for page in doc.pages:
        found = _search_glossary_div(page._page_box)
        if found is not None:
            return found
    raise AssertionError('<div class="glossary..."> not found in any page')


def _search_glossary_div(box) -> float | None:
    element = getattr(box, "element", None)
    classes = (element.get("class") or "").split() if element is not None else []
    if getattr(element, "tag", None) == "div" and "glossary" in classes:
        return box.width
    for child in getattr(box, "children", None) or []:
        found = _search_glossary_div(child)
        if found is not None:
            return found
    return None


def _contains_text(box, marker_text: str) -> bool:
    text = getattr(box, "text", None)
    if text and marker_text.casefold() in text.casefold():
        return True
    return any(_contains_text(child, marker_text) for child in getattr(box, "children", None) or [])


def _glossary_div(html: str) -> str:
    match = GLOSSARY_DIV_RE.search(html)
    assert match is not None, "glossary div not found in rendered HTML"
    return match.group(0)


def _glossary_terms_html(html: str) -> str:
    div = _glossary_div(html)
    return div.split(">", 1)[1]


def test_glossary_spanning_true_title_spans_both_columns():
    html = _render([_paragraph("filler"), _glossary("SPANMARKER", spanning=True)])
    standard_width = _find_block_width(html, "filler", "p")
    spanning_width = _find_block_width(html, "SPANMARKER", "h2")
    assert spanning_width > standard_width * 1.5


def test_glossary_spanning_true_term_list_also_spans_both_columns():
    # Regression: a long (non-spanning) term list fragments across the outer 2-column
    # layout, and since .glossary sets its own column-count: 2, each outer fragment gets
    # its own 2 sub-columns — 4 visible columns instead of 2. Spanning must apply to the
    # glossary div itself (not just its title) so it renders as one full-width, 2-column
    # block, matching real CORE ABILITIES content (36 terms) on page 2 of the 11e sheet.
    html = _render([_paragraph("filler"), _glossary("SPANMARKER", spanning=True)])
    standard_width = _find_block_width(html, "filler", "p")
    spanning_width = _find_glossary_div_width(html)
    assert spanning_width > standard_width * 1.5


def test_glossary_term_list_content_identical_regardless_of_spanning_flag():
    # Spanning adds a `.block--full-width` wrapper around the glossary div, but the
    # terms themselves render identically either way.
    spanning_html = _render([_glossary("TITLE", spanning=True)])
    non_spanning_html = _render([_glossary("TITLE", spanning=False)])
    assert _glossary_terms_html(spanning_html) == _glossary_terms_html(non_spanning_html)


def test_glossary_spanning_omitted_matches_pre_addition_rendering():
    html = _render([_glossary("CORE ABILITIES")])
    assert '<h2 class="phase">CORE ABILITIES</h2>' in html
    assert '<h2 class="phase phase--spanning">CORE ABILITIES</h2>' not in html


def test_glossary_spanning_false_matches_omitted_rendering():
    omitted_html = _render([_glossary("CORE ABILITIES")])
    false_html = _render([_glossary("CORE ABILITIES", spanning=False)])
    assert omitted_html == false_html


def test_spanning_glossary_at_a_page_boundary_does_not_crash_layout():
    # Regression (2026-09-02): an element that is BOTH a multi-column container
    # (`.glossary` sets `column-count: 2`) AND spans its parent's columns
    # (`column-span: all`) crashes WeasyPrint's layout engine with a bare `AssertionError`
    # ("assert not page_is_empty", weasyprint/layout/page.py) whenever the block lands at a
    # page boundary. Real 11e German content hit this once enough text had been added ahead
    # of the CORE ABILITIES glossary. Fixed by splitting the two roles across two elements:
    # a `.block--full-width` wrapper spans, the inner `.glossary` keeps its own columns.
    # Sweeping the filler count walks the glossary across a page boundary; every amount must
    # render. Needs a realistically tall glossary -- a two-term one never reaches the seam.
    tall_glossary = {
        "type": "glossary",
        "title": "CORE ABILITIES",
        "spanning": True,
        "terms": [
            {"term": f"TERM {i:02d}", "text": "A description with enough text that the entry wraps realistically."}
            for i in range(35)
        ],
    }
    for filler_count in range(20, 46, 2):
        blocks = [_paragraph(f"Filler paragraph {i} " + "word " * 28) for i in range(filler_count)]
        blocks.append(tall_glossary)
        html = _render(blocks)
        weasyprint.HTML(string=html, base_url=str(TEMPLATES_ROOT)).render()
