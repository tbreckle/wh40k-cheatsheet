import copy
from pathlib import Path

from wh40k_cheatsheet.content import resolve_content
from wh40k_cheatsheet.content.sections import SECTION_IDS, has_section_markers
from wh40k_cheatsheet.render.html_renderer import render_html
from wh40k_cheatsheet.revision import discover_revisions

REPO_ROOT = Path(__file__).resolve().parents[2]
EDITIONS_ROOT = REPO_ROOT / "editions"
TEMPLATES_ROOT = REPO_ROOT / "templates"

# Every (edition, language) shipped with content, and the section ids that edition's sheet
# actually declares.
SHIPPED_EDITIONS_LANGUAGES_SECTIONS = [
    ("11e", "en", frozenset(SECTION_IDS)),
    ("11e", "de", frozenset(SECTION_IDS)),
]


def _latest_revision(edition_id: str) -> str:
    return str(discover_revisions(EDITIONS_ROOT, edition_id).latest().id)


def _real_content(edition_id: str, language: str) -> dict:
    revision_id = _latest_revision(edition_id)
    return resolve_content(EDITIONS_ROOT, edition_id, revision_id, language)


def _marker_ids(blocks: list[dict]) -> set[str]:
    return {block["id"] for block in blocks if isinstance(block, dict) and block.get("type") == "section"}


def _without_section_blocks(blocks: list[dict]) -> list[dict]:
    return [block for block in blocks if not (isinstance(block, dict) and block.get("type") == "section")]


def test_every_shipped_document_declares_its_full_section_set():
    for edition_id, language, expected_ids in SHIPPED_EDITIONS_LANGUAGES_SECTIONS:
        content = _real_content(edition_id, language)
        blocks = content["document"]["blocks"]
        assert has_section_markers(blocks), f"{edition_id}/{language}: no section markers found"
        assert _marker_ids(blocks) == expected_ids, f"{edition_id}/{language}: unexpected section id set"


def test_section_markers_do_not_change_rendered_html():
    for edition_id, language, _ in SHIPPED_EDITIONS_LANGUAGES_SECTIONS:
        content = _real_content(edition_id, language)
        with_markers_html = render_html(TEMPLATES_ROOT, "cheatsheet.html.j2", content)

        without_markers = copy.deepcopy(content)
        without_markers["document"]["blocks"] = _without_section_blocks(without_markers["document"]["blocks"])
        without_markers_html = render_html(TEMPLATES_ROOT, "cheatsheet.html.j2", without_markers)

        assert with_markers_html == without_markers_html, f"{edition_id}/{language}: markers changed rendered HTML"
