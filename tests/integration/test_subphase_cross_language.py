from pathlib import Path

import weasyprint

from wh40k_cheatsheet.render.html_renderer import render_html

TEMPLATES_ROOT = Path(__file__).resolve().parents[2] / "templates"


def _document(language: str, blocks: list[dict]) -> dict:
    return {"document": {"title": "Test", "language": language, "blocks": blocks}}


def _phase(title: str) -> dict:
    return {"type": "phase", "title": title}


def _subphase(title: str) -> dict:
    return {"type": "subphase", "title": title}


def _render(document: dict) -> str:
    return render_html(TEMPLATES_ROOT, "cheatsheet.html.j2", document)


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


def test_equivalent_subphase_placement_renders_the_same_brighter_color_across_languages():
    en = _document("en", [_phase("ENGLISHPHASE"), _subphase("ENGLISHSUB")])
    de = _document("de", [_phase("DEUTSCHPHASE"), _subphase("DEUTSCHSUB")])

    en_html = _render(en)
    de_html = _render(de)

    en_phase_bg = _find_block(en_html, "ENGLISHPHASE", "h2").style["background_color"]
    en_sub_bg = _find_block(en_html, "ENGLISHSUB", "h2").style["background_color"]
    de_phase_bg = _find_block(de_html, "DEUTSCHPHASE", "h2").style["background_color"]
    de_sub_bg = _find_block(de_html, "DEUTSCHSUB", "h2").style["background_color"]

    assert _luminance(en_sub_bg) > _luminance(en_phase_bg)
    assert _luminance(de_sub_bg) > _luminance(de_phase_bg)
    assert en_sub_bg.coordinates == de_sub_bg.coordinates
    assert en_phase_bg.coordinates == de_phase_bg.coordinates
