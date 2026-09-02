import copy
import re
import unicodedata
from html import unescape
from itertools import pairwise
from pathlib import Path

from wh40k_cheatsheet.content import resolve_content
from wh40k_cheatsheet.render.html_renderer import render_html
from wh40k_cheatsheet.revision import discover_revisions

REPO_ROOT = Path(__file__).resolve().parents[2]
EDITIONS_ROOT = REPO_ROOT / "editions"
TEMPLATES_ROOT = REPO_ROOT / "templates"

# Every (edition, language) known to declare a `glossary` block, per project.yaml/content.yaml.
GLOSSARY_EDITIONS_LANGUAGES = [("11e", "en"), ("11e", "de"), ("10e", "de")]


def _fold(term: str) -> str:
    folded = unicodedata.normalize("NFD", term.casefold())
    return "".join(c for c in folded if not unicodedata.combining(c))


def _latest_revision(edition_id: str) -> str:
    return str(discover_revisions(EDITIONS_ROOT, edition_id).latest().id)


def _real_content(edition_id: str, language: str) -> dict:
    revision_id = _latest_revision(edition_id)
    return resolve_content(EDITIONS_ROOT, edition_id, revision_id, language)


def _glossary_entries(content: dict) -> list[dict]:
    for block in content["document"]["blocks"]:
        if block.get("type") == "glossary":
            return block["terms"]
    raise AssertionError("no glossary block found in content")


def _render(content: dict) -> str:
    return render_html(TEMPLATES_ROOT, "cheatsheet.html.j2", content)


def _rendered_term_names(rendered_html: str) -> list[str]:
    match = re.search(r'<div class="glossary[^"]*">(.*?)</div>', rendered_html, re.DOTALL)
    assert match is not None, "no glossary div found in rendered HTML"
    return [unescape(term) for term in re.findall(r'<span class="term__name">(.*?):</span>', match.group(1))]


def _rendered_term_bodies(rendered_html: str) -> list[str]:
    match = re.search(r'<div class="glossary[^"]*">(.*?)</div>', rendered_html, re.DOTALL)
    assert match is not None, "no glossary div found in rendered HTML"
    return re.findall(r'<p class="term">.*?</span>\s*(.*?)</p>', match.group(1), re.DOTALL)


def test_every_real_glossary_renders_in_ascending_alphabetical_order():
    for edition_id, language in GLOSSARY_EDITIONS_LANGUAGES:
        content = _real_content(edition_id, language)
        rendered_terms = _rendered_term_names(_render(content))

        assert len(rendered_terms) > 1, f"{edition_id}/{language}: expected multiple glossary terms"
        for earlier, later in pairwise(rendered_terms):
            assert _fold(earlier) <= _fold(later), (
                f"{edition_id}/{language}: '{earlier}' should not precede '{later}' alphabetically"
            )


def test_every_real_glossary_preserves_entry_count_and_definitions():
    for edition_id, language in GLOSSARY_EDITIONS_LANGUAGES:
        content = _real_content(edition_id, language)
        authored = _glossary_entries(content)
        rendered_terms = _rendered_term_names(_render(content))

        assert len(rendered_terms) == len(authored), f"{edition_id}/{language}: entry count changed"
        assert set(rendered_terms) == {entry["term"] for entry in authored}, (
            f"{edition_id}/{language}: term set changed"
        )


def test_english_11e_glossary_output_is_unchanged_by_sorting():
    content = _real_content("11e", "en")
    authored_terms = [entry["term"] for entry in _glossary_entries(content)]
    rendered_terms = _rendered_term_names(_render(content))

    assert rendered_terms == authored_terms


def test_print_friendly_render_yields_the_same_glossary_order_as_standard():
    content = _real_content("11e", "de")
    standard_html = _render(content)

    print_content = {**content, "document": {**content["document"], "print_friendly": True}}
    print_html = _render(print_content)

    assert _rendered_term_names(print_html) == _rendered_term_names(standard_html)


def test_reversing_authored_glossary_order_does_not_change_rendered_output():
    content = _real_content("11e", "de")
    forward_html = _render(content)

    reversed_content = copy.deepcopy(content)
    for block in reversed_content["document"]["blocks"]:
        if block.get("type") == "glossary":
            block["terms"] = list(reversed(block["terms"]))
    reversed_html = _render(reversed_content)

    assert _rendered_term_names(reversed_html) == _rendered_term_names(forward_html)
    assert _rendered_term_bodies(reversed_html) == _rendered_term_bodies(forward_html)
