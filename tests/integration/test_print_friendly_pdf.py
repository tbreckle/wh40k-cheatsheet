import math
import re
import shutil
from pathlib import Path

import weasyprint

from wh40k_cheatsheet.cli import main
from wh40k_cheatsheet.config import load_project_config
from wh40k_cheatsheet.pipeline import Paths, generate
from wh40k_cheatsheet.render.html_renderer import render_html

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_ROOT = REPO_ROOT / "templates"

# Style properties that can carry a color on any rendered box.
_COLOR_PROPS = (
    "color",
    "background_color",
    "border_top_color",
    "border_bottom_color",
    "border_left_color",
    "border_right_color",
)


def _paths() -> Paths:
    return Paths(
        editions_root=REPO_ROOT / "editions",
        templates_root=REPO_ROOT / "templates",
        out_root=REPO_ROOT / "out",
        images_root=REPO_ROOT / "images",
    )


def _project_root(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    shutil.copy(REPO_ROOT / "project.yaml", root / "project.yaml")
    shutil.copytree(REPO_ROOT / "editions", root / "editions")
    shutil.copytree(REPO_ROOT / "templates", root / "templates")
    shutil.copytree(REPO_ROOT / "images", root / "images")
    return root


def _document(blocks: list[dict], *, print_friendly: bool | None = None) -> dict:
    document = {"title": "Test", "language": "en", "blocks": blocks}
    if print_friendly is not None:
        document["print_friendly"] = print_friendly
    return {"document": document}


def _render(blocks: list[dict], *, print_friendly: bool | None = None) -> str:
    return render_html(TEMPLATES_ROOT, "cheatsheet.html.j2", _document(blocks, print_friendly=print_friendly))


def _render_doc(blocks: list[dict], *, print_friendly: bool | None = None):
    html = _render(blocks, print_friendly=print_friendly)
    return weasyprint.HTML(string=html, base_url=str(TEMPLATES_ROOT)).render()


def _all_boxes(box):
    yield box
    for child in getattr(box, "children", None) or []:
        yield from _all_boxes(child)


def _all_pages_boxes(rendered):
    for page in rendered.pages:
        yield from _all_boxes(page._page_box)


def _is_grayscale(color) -> bool:
    r, g, b = color.coordinates
    return math.isclose(r, g, abs_tol=1e-6) and math.isclose(g, b, abs_tol=1e-6)


def _non_grayscale_colors(rendered) -> list[tuple[str, tuple, str | None]]:
    """Every non-grayscale, non-transparent color found across every box/page of `rendered`."""
    findings = []
    for box in _all_pages_boxes(rendered):
        for prop in _COLOR_PROPS:
            try:
                color = box.style[prop]
            except KeyError:
                continue
            if isinstance(color, str) or color is None:  # "currentcolor" or unset
                continue
            if getattr(color, "alpha", 1) == 0:
                continue
            if not _is_grayscale(color):
                element = getattr(box, "element", None)
                tag = getattr(element, "tag", None)
                findings.append((prop, color.coordinates, tag))
    return findings


def _find_box_by_class(rendered, class_name: str):
    for box in _all_pages_boxes(rendered):
        element = getattr(box, "element", None)
        classes = (element.get("class") if element is not None else None) or ""
        if class_name in classes.split():
            return box
    raise AssertionError(f"no box found with class '{class_name}'")


def _find_box_by_exact_classes(rendered, *class_names: str):
    wanted = set(class_names)
    for box in _all_pages_boxes(rendered):
        element = getattr(box, "element", None)
        classes = (element.get("class") if element is not None else None) or ""
        if set(classes.split()) == wanted:
            return box
    raise AssertionError(f"no box found with exact classes {wanted}")


# A synthetic document covering every color-bearing block/variant in the template: all three
# phase levels (phase, subphase, subsection), both callout variants, a multi-row table (zebra
# striping), and all three stratagem timing variants.
_ALL_VARIANTS_BLOCKS = [
    {"type": "phase", "title": "1. COMMAND PHASE"},
    {"type": "subphase", "title": "1a. Battle-shock Step"},
    {"type": "subsection", "title": "Battle-Shock"},
    {"type": "callout", "text": "warn callout", "variant": "warn"},
    {"type": "callout", "text": "info callout", "variant": "info"},
    {
        "type": "table",
        "columns": ["A", "B"],
        "rows": [["r1c1", "r1c2"], ["r2c1", "r2c2"], ["r3c1", "r3c2"]],
    },
    {
        "type": "stratagem",
        "title": "YOUR STRATAGEM",
        "cost": "1CP",
        "timing": "your",
        "effect": "effect text",
    },
    {
        "type": "stratagem",
        "title": "OPPONENT STRATAGEM",
        "cost": "1CP",
        "timing": "opponent",
        "effect": "effect text",
    },
    {
        "type": "stratagem",
        "title": "EITHER STRATAGEM",
        "cost": "1CP",
        "timing": "either",
        "effect": "effect text",
    },
    {"type": "glossary", "title": "CORE ABILITIES", "terms": [{"term": "ASSAULT", "text": "text"}]},
]


def test_print_friendly_rendering_uses_only_grayscale_colors():
    rendered = _render_doc(_ALL_VARIANTS_BLOCKS, print_friendly=True)
    findings = _non_grayscale_colors(rendered)
    assert not findings, f"non-grayscale colors found in print-friendly rendering: {findings[:10]}"


def test_standard_rendering_still_uses_color_when_flag_omitted():
    # Sanity check for the test helpers themselves: the same content, without the flag,
    # must still contain non-grayscale colors (e.g. the green phase header).
    rendered = _render_doc(_ALL_VARIANTS_BLOCKS)
    findings = _non_grayscale_colors(rendered)
    assert findings, "expected non-grayscale colors in the standard (non-print-friendly) rendering"


def test_print_friendly_stratagem_timing_variants_remain_distinguishable():
    rendered = _render_doc(_ALL_VARIANTS_BLOCKS, print_friendly=True)
    your_bg = _find_box_by_class(rendered, "stratagem__timing--your").style["background_color"].coordinates
    opponent_bg = _find_box_by_class(rendered, "stratagem__timing--opponent").style["background_color"].coordinates
    either_bg = _find_box_by_class(rendered, "stratagem__timing--either").style["background_color"].coordinates
    assert your_bg != opponent_bg
    assert your_bg != either_bg
    assert opponent_bg != either_bg


def test_print_friendly_subphase_remains_distinguishable_from_phase():
    rendered = _render_doc(_ALL_VARIANTS_BLOCKS, print_friendly=True)
    phase_bg = _find_box_by_exact_classes(rendered, "phase").style["background_color"].coordinates
    subphase_bg = _find_box_by_class(rendered, "phase--sub").style["background_color"].coordinates
    assert phase_bg != subphase_bg


def test_print_friendly_callout_variants_remain_distinguishable():
    rendered = _render_doc(_ALL_VARIANTS_BLOCKS, print_friendly=True)
    warn_bg = _find_box_by_class(rendered, "callout--warn").style["background_color"].coordinates
    info_bg = _find_box_by_class(rendered, "callout--info").style["background_color"].coordinates
    assert warn_bg != info_bg


def test_print_friendly_watermark_absent_on_every_page_real_content():
    config = load_project_config(REPO_ROOT / "project.yaml")
    paths = _paths()
    doc = generate(config, paths, "11e", language="en", print_friendly=True)[0]
    html = doc.print_html_path.read_text(encoding="utf-8")
    rendered = weasyprint.HTML(string=html, base_url=str(paths.templates_root)).render()

    assert len(rendered.pages) >= 1
    for box in _all_pages_boxes(rendered):
        element = getattr(box, "element", None)
        assert getattr(element, "tag", None) != "img", "watermark <img> box found in print-friendly rendering"
    assert "<img" not in html


def _cheatsheet_article(html: str) -> str:
    match = re.search(r'<article class="cheatsheet">.*</article>', html, re.DOTALL)
    assert match, 'expected <article class="cheatsheet"> in rendered HTML'
    return match.group(0)


def test_print_friendly_content_and_page_count_match_standard_rendering():
    config = load_project_config(REPO_ROOT / "project.yaml")
    paths = _paths()

    for language in ("en", "de"):
        doc = generate(config, paths, "11e", language=language, print_friendly=True)[0]
        standard_html = doc.html_path.read_text(encoding="utf-8")
        print_html = doc.print_html_path.read_text(encoding="utf-8")

        assert _cheatsheet_article(standard_html) == _cheatsheet_article(print_html)

        standard_pages = len(weasyprint.HTML(string=standard_html, base_url=str(paths.templates_root)).render().pages)
        print_pages = len(weasyprint.HTML(string=print_html, base_url=str(paths.templates_root)).render().pages)
        assert standard_pages == print_pages


def test_cli_print_friendly_flag_writes_both_pdfs_and_reports_both_paths(tmp_path, capsys):
    root = _project_root(tmp_path)

    exit_code = main(
        ["--project-root", str(root), "generate", "--edition", "11e", "--language", "en", "--print-friendly"]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    out_dir = root / "out" / "11e"
    revision_dir = next(out_dir.iterdir())
    assert (revision_dir / "en.pdf").is_file()
    assert (revision_dir / "en.html").is_file()
    assert (revision_dir / "en-print.pdf").is_file()
    assert (revision_dir / "en-print.html").is_file()

    assert str(revision_dir / "en.pdf") in captured.out
    assert str(revision_dir / "en-print.pdf") in captured.out
    assert "(print-friendly)" in captured.out


def test_cli_omitting_print_friendly_flag_writes_only_standard_pdf(tmp_path, capsys):
    root = _project_root(tmp_path)

    exit_code = main(["--project-root", str(root), "generate", "--edition", "11e", "--language", "en"])
    captured = capsys.readouterr()

    assert exit_code == 0
    out_dir = root / "out" / "11e"
    revision_dir = next(out_dir.iterdir())
    assert (revision_dir / "en.pdf").is_file()
    assert not (revision_dir / "en-print.pdf").exists()
    assert not (revision_dir / "en-print.html").exists()
    assert "(print-friendly)" not in captured.out
    assert captured.out.count("\n") == 1
