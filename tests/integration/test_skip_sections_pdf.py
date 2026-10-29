import re
import shutil
from pathlib import Path

import pytest
import weasyprint

from wh40k_cheatsheet.config import load_project_config
from wh40k_cheatsheet.content import ContentError
from wh40k_cheatsheet.pipeline import Paths, PipelineError, generate

REPO_ROOT = Path(__file__).resolve().parents[2]

# Section id -> (11e `en` signature, 11e `de` signature), each unique to that section's region
# (verified against the real rendered HTML; see specs/015-skip-sheet-sections/tasks.md).
SECTION_SIGNATURES = {
    "core-rules": ("1. COMMAND PHASE (08)", "1. BEFEHLSPHASE (08)"),
    "core-abilities": ("CORE ABILITIES", "KERNFÄHIGKEITEN"),
    "datasheet-characteristics": ("DATASHEET CHARACTERISTICS", "DATENBLATT-KENNWERTE"),
    "core-stratagems": ("STRATAGEMS", "GEFECHTSOPTIONEN"),
}
ALL_SECTION_IDS = tuple(SECTION_SIGNATURES)


def _project_root(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    shutil.copy(REPO_ROOT / "project.yaml", root / "project.yaml")
    shutil.copytree(REPO_ROOT / "editions", root / "editions")
    shutil.copytree(REPO_ROOT / "templates", root / "templates")
    return root


def _paths(root: Path) -> Paths:
    return Paths(
        editions_root=root / "editions",
        templates_root=root / "templates",
        out_root=root / "out",
    )


def _render_pages(html_path: Path, root: Path):
    html = html_path.read_text(encoding="utf-8")
    return weasyprint.HTML(string=html, base_url=str(root / "templates")).render().pages


def _has_class(box, name: str) -> bool:
    element = getattr(box, "element", None)
    classes = (element.get("class") if element is not None else None) or ""
    return name in classes.split()


def _page_has_sheet_text(page) -> bool:
    def walk(box, inside_sheet: bool) -> bool:
        inside_sheet = inside_sheet or _has_class(box, "sheet")
        text = getattr(box, "text", None)
        if inside_sheet and text and text.strip():
            return True
        return any(walk(child, inside_sheet) for child in getattr(box, "children", None) or [])

    return walk(page._page_box, False)


def test_every_page_has_content_for_every_single_section_skip(tmp_path):
    root = _project_root(tmp_path)
    config = load_project_config(root / "project.yaml")
    for section_id in ALL_SECTION_IDS:
        doc = generate(config, _paths(root), "11e", language="en", skip_sections=frozenset({section_id}))[0]
        pages = _render_pages(doc.html_path, root)
        assert pages, f"{section_id}: no pages rendered"
        for i, page in enumerate(pages):
            assert _page_has_sheet_text(page), f"{section_id}: page {i} has no sheet content (blank page)"


@pytest.mark.parametrize("section_id", ALL_SECTION_IDS)
def test_skipping_one_section_omits_it_and_keeps_the_rest(tmp_path, section_id):
    root = _project_root(tmp_path)
    config = load_project_config(root / "project.yaml")

    doc = generate(config, _paths(root), "11e", language="en", skip_sections=frozenset({section_id}))[0]

    assert doc.pdf_path.name == f"en-no-{section_id}.pdf"
    assert doc.html_path.name == f"en-no-{section_id}.html"
    assert doc.omitted_sections == (section_id,)

    html = doc.html_path.read_text(encoding="utf-8")
    en_signature, _ = SECTION_SIGNATURES[section_id]
    assert en_signature not in html

    for other_id, (other_signature, _) in SECTION_SIGNATURES.items():
        if other_id != section_id:
            assert other_signature in html, f"{other_id}'s signature missing after skipping {section_id}"


def test_skipping_core_stratagems_yields_fewer_pages_than_full_sheet(tmp_path):
    root = _project_root(tmp_path)
    config = load_project_config(root / "project.yaml")

    full_doc = generate(config, _paths(root), "11e", language="en")[0]
    partial_doc = generate(config, _paths(root), "11e", language="en", skip_sections=frozenset({"core-stratagems"}))[0]

    assert len(_render_pages(partial_doc.html_path, root)) < len(_render_pages(full_doc.html_path, root))


def test_skipping_core_rules_starts_the_sheet_with_core_abilities(tmp_path):
    root = _project_root(tmp_path)
    config = load_project_config(root / "project.yaml")

    doc = generate(config, _paths(root), "11e", language="en", skip_sections=frozenset({"core-rules"}))[0]
    pages = _render_pages(doc.html_path, root)
    assert pages  # sanity: still renders pages, no error
    # CORE ABILITIES must be the first heading-bearing content, i.e. it appears before any
    # other remaining section's signature.
    html = doc.html_path.read_text(encoding="utf-8")
    core_abilities_index = html.index("CORE ABILITIES")
    for other_id in ("datasheet-characteristics", "core-stratagems"):
        other_signature, _ = SECTION_SIGNATURES[other_id]
        assert core_abilities_index < html.index(other_signature)


def test_generating_full_sheet_then_a_skip_leaves_full_sheet_untouched(tmp_path):
    root = _project_root(tmp_path)
    config = load_project_config(root / "project.yaml")

    full_doc = generate(config, _paths(root), "11e", language="en")[0]
    full_html_before = full_doc.html_path.read_bytes()
    full_pdf_before = full_doc.pdf_path.read_bytes()

    generate(config, _paths(root), "11e", language="en", skip_sections=frozenset({"core-stratagems"}))

    assert full_doc.html_path.read_bytes() == full_html_before
    assert full_doc.pdf_path.read_bytes() == full_pdf_before


def test_generate_without_skip_sections_is_unchanged(tmp_path):
    root = _project_root(tmp_path)
    config = load_project_config(root / "project.yaml")

    doc = generate(config, _paths(root), "11e", language="en")[0]

    assert doc.pdf_path.name == "en.pdf"
    assert doc.omitted_sections == ()


def test_generate_rejects_invalid_section_id(tmp_path):
    root = _project_root(tmp_path)
    config = load_project_config(root / "project.yaml")

    with pytest.raises(PipelineError) as exc_info:
        generate(config, _paths(root), "11e", language="en", skip_sections=frozenset({"stratagems"}))

    message = str(exc_info.value)
    assert "stratagems" in message
    for section_id in ALL_SECTION_IDS:
        assert section_id in message


def test_skipping_two_sections_combines_into_one_ordered_file_name(tmp_path):
    root = _project_root(tmp_path)
    config = load_project_config(root / "project.yaml")

    doc = generate(
        config,
        _paths(root),
        "11e",
        language="en",
        skip_sections=frozenset({"core-rules", "core-stratagems"}),
    )[0]

    assert doc.pdf_path.name == "en-no-core-rules-core-stratagems.pdf"
    assert doc.omitted_sections == ("core-rules", "core-stratagems")

    html = doc.html_path.read_text(encoding="utf-8")
    assert SECTION_SIGNATURES["core-abilities"][0] in html
    assert SECTION_SIGNATURES["datasheet-characteristics"][0] in html
    assert SECTION_SIGNATURES["core-rules"][0] not in html
    assert SECTION_SIGNATURES["core-stratagems"][0] not in html


def test_skipping_three_sections_leaves_only_the_fourth_with_no_blank_page(tmp_path):
    root = _project_root(tmp_path)
    config = load_project_config(root / "project.yaml")

    keep = "core-abilities"
    skip = frozenset(sid for sid in ALL_SECTION_IDS if sid != keep)
    doc = generate(config, _paths(root), "11e", language="en", skip_sections=skip)[0]

    html = doc.html_path.read_text(encoding="utf-8")
    assert SECTION_SIGNATURES[keep][0] in html
    for other_id in skip:
        assert SECTION_SIGNATURES[other_id][0] not in html

    for page in _render_pages(doc.html_path, root):
        assert _page_has_sheet_text(page)


def test_generate_rejects_omitting_all_four_sections(tmp_path):
    root = _project_root(tmp_path)
    config = load_project_config(root / "project.yaml")

    with pytest.raises(PipelineError) as exc_info:
        generate(config, _paths(root), "11e", skip_sections=frozenset(ALL_SECTION_IDS))
    assert "no content" in str(exc_info.value)
    assert not (root / "out").exists()


def test_multilanguage_run_fails_before_writing_any_language_if_one_would_be_empty(tmp_path):
    root = _project_root(tmp_path)
    de_content_path = root / "editions" / "11e" / "2026-06-01-00" / "de" / "content.yaml"
    de_content_path.write_text(
        """
document:
  title: "Test"
  language: "de"
  blocks:
    - type: section
      id: core-rules
    - type: paragraph
      text: "only core rules content"
""",
        encoding="utf-8",
    )
    config = load_project_config(root / "project.yaml")

    with pytest.raises(PipelineError):
        generate(config, _paths(root), "11e", skip_sections=frozenset({"core-rules"}))

    assert not list((root / "out" / "11e").glob("**/en*.pdf"))
    assert not list((root / "out" / "11e").glob("**/de*.pdf"))


def _cheatsheet_article(html: str) -> str:
    match = re.search(r'<article class="cheatsheet">.*</article>', html, re.DOTALL)
    assert match, 'expected <article class="cheatsheet"> in rendered HTML'
    return match.group(0)


def test_print_friendly_and_multilanguage_all_omit_the_same_section(tmp_path):
    root = _project_root(tmp_path)
    config = load_project_config(root / "project.yaml")

    docs = generate(
        config,
        _paths(root),
        "11e",
        print_friendly=True,
        skip_sections=frozenset({"datasheet-characteristics"}),
    )
    by_language = {doc.language: doc for doc in docs}
    assert set(by_language) == {"en", "de"}

    for language, doc in by_language.items():
        assert doc.pdf_path.name == f"{language}-no-datasheet-characteristics.pdf"
        assert doc.print_pdf_path.name == f"{language}-no-datasheet-characteristics-print.pdf"
        assert doc.omitted_sections == ("datasheet-characteristics",)

        standard_html = doc.html_path.read_text(encoding="utf-8")
        print_html = doc.print_html_path.read_text(encoding="utf-8")
        assert "DATASHEET CHARACTERISTICS" not in standard_html
        assert "DATENBLATT-KENNWERTE" not in standard_html
        assert "DATASHEET CHARACTERISTICS" not in print_html
        assert "DATENBLATT-KENNWERTE" not in print_html
        # Same content (only color differs) between standard and print-friendly.
        assert _cheatsheet_article(standard_html) == _cheatsheet_article(print_html)


def test_generate_rejects_skip_against_content_with_no_section_markers(tmp_path):
    root = _project_root(tmp_path)
    content_path = root / "editions" / "11e" / "2026-06-01-00" / "en" / "content.yaml"
    text = content_path.read_text(encoding="utf-8")
    stripped_lines = []
    skip_next_id_line = False
    for line in text.splitlines(keepends=True):
        if skip_next_id_line:
            skip_next_id_line = False
            continue
        if line.strip() == "- type: section":
            skip_next_id_line = True
            continue
        stripped_lines.append(line)
    content_path.write_text("".join(stripped_lines), encoding="utf-8")

    config = load_project_config(root / "project.yaml")

    with pytest.raises(ContentError) as exc_info:
        generate(config, _paths(root), "11e", language="en", skip_sections=frozenset({"core-rules"}))
    assert str(content_path) in str(exc_info.value)
    assert "no section markers" in str(exc_info.value)

    # Without skip_sections, the same (now marker-less) content still generates fine.
    doc = generate(config, _paths(root), "11e", language="en")[0]
    assert doc.pdf_path.name == "en.pdf"
