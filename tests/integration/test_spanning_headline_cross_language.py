from pathlib import Path

import weasyprint

from wh40k_cheatsheet.render.html_renderer import render_html

TEMPLATES_ROOT = Path(__file__).resolve().parents[2] / "templates"


def _document(language: str, blocks: list[dict]) -> dict:
    return {"document": {"title": "Test", "language": language, "blocks": blocks}}


def _paragraph(text: str) -> dict:
    return {"type": "paragraph", "text": text}


def _spanning(title: str) -> dict:
    return {"type": "spanning_headline", "title": title}


def _render(document: dict) -> str:
    return render_html(TEMPLATES_ROOT, "cheatsheet.html.j2", document)


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


def test_equivalent_spanning_headline_placement_renders_full_width_across_languages():
    en = _document("en", [_paragraph("filler"), _spanning("ENGLISHSPAN")])
    de = _document("de", [_paragraph("Fuellinhalt"), _spanning("GERMANSPAN")])

    en_html = _render(en)
    de_html = _render(de)

    en_filler_width = _find_block_width(en_html, "filler", "p")
    en_span_width = _find_block_width(en_html, "ENGLISHSPAN", "h2")
    de_filler_width = _find_block_width(de_html, "Fuellinhalt", "p")
    de_span_width = _find_block_width(de_html, "GERMANSPAN", "h2")

    assert en_span_width > en_filler_width * 1.5
    assert de_span_width > de_filler_width * 1.5
