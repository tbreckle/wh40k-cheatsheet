import math
import shutil
from pathlib import Path

import pytest
import weasyprint

from wh40k_cheatsheet.cli import main
from wh40k_cheatsheet.config import load_project_config
from wh40k_cheatsheet.pdf import PdfError
from wh40k_cheatsheet.pipeline import Paths, generate

REPO_ROOT = Path(__file__).resolve().parents[2]
LOGO_ASPECT_RATIO = 2184 / 668
# Pre-rotation display size (research.md §1): rotated bounding box is a square whose
# side equals the page width, the binding constraint for A4 portrait.
EXPECTED_WIDTH_PX = 227.42 / 25.4 * 96
EXPECTED_HEIGHT_PX = EXPECTED_WIDTH_PX / LOGO_ASPECT_RATIO
EXPECTED_ROTATION_RAD = math.pi / 4
EXPECTED_OPACITY = 0.05


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


def _all_boxes(box):
    yield box
    for child in getattr(box, "children", None) or []:
        yield from _all_boxes(child)


def _watermark_box(page):
    for box in _all_boxes(page._page_box):
        element = getattr(box, "element", None)
        if getattr(element, "tag", None) == "img":
            return box
    raise AssertionError("watermark <img> box not found on page")


def _render_real_content(language: str):
    config = load_project_config(REPO_ROOT / "project.yaml")
    paths = _paths()
    doc = generate(config, paths, "11e", language=language)[0]
    html = doc.html_path.read_text(encoding="utf-8")
    return weasyprint.HTML(string=html, base_url=str(paths.templates_root)).render()


def test_watermark_present_correct_size_rotation_and_opacity_on_every_page():
    rendered = _render_real_content("en")
    assert len(rendered.pages) >= 1
    for page in rendered.pages:
        box = _watermark_box(page)
        # transform is paint-time only; the box's own layout size is the pre-rotation size.
        assert box.width == pytest.approx(EXPECTED_WIDTH_PX, rel=0.01)
        assert box.height == pytest.approx(EXPECTED_HEIGHT_PX, rel=0.01)

        rotations = [value for kind, value in box.style["transform"] if kind == "rotate"]
        assert rotations, "no rotate() transform found on the watermark"
        assert rotations[0] == pytest.approx(EXPECTED_ROTATION_RAD, rel=0.001)

        assert box.style["opacity"] == pytest.approx(EXPECTED_OPACITY, rel=0.001)


def test_watermark_same_position_on_every_page_both_languages():
    for language in ("en", "de"):
        rendered = _render_real_content(language)
        positions = {
            (round(_watermark_box(p).position_x, 1), round(_watermark_box(p).position_y, 1)) for p in rendered.pages
        }
        assert len(positions) == 1, f"watermark position varies across pages for language={language}: {positions}"


def test_watermark_appears_before_content_in_dom_order():
    # No z-index is set (research.md §4 — a negative value hides the watermark entirely),
    # so DOM order is what keeps it painting behind the document's own content.
    config = load_project_config(REPO_ROOT / "project.yaml")
    paths = _paths()
    doc = generate(config, paths, "11e", language="en")[0]
    html = doc.html_path.read_text(encoding="utf-8")

    watermark_index = html.index('class="page-watermark"')
    content_index = html.index('class="cheatsheet"')
    assert watermark_index < content_index


def test_regenerating_real_content_keeps_same_page_count():
    config = load_project_config(REPO_ROOT / "project.yaml")
    paths = _paths()
    en_pages = len(
        weasyprint.HTML(
            string=generate(config, paths, "11e", language="en")[0].html_path.read_text(encoding="utf-8"),
            base_url=str(paths.templates_root),
        )
        .render()
        .pages
    )
    de_pages = len(
        weasyprint.HTML(
            string=generate(config, paths, "11e", language="de")[0].html_path.read_text(encoding="utf-8"),
            base_url=str(paths.templates_root),
        )
        .render()
        .pages
    )
    # Baseline after this amendment: the @page top margin reverted from 15mm (needed only
    # by the old corner logo) back to 7mm, giving both languages more usable space per page.
    assert en_pages == 3
    assert de_pages == 4


def test_missing_logo_asset_fails_generation_via_cli(tmp_path, capsys):
    root = _project_root(tmp_path)
    (root / "images" / "logo_40k.png").unlink()

    exit_code = main(["--project-root", str(root), "generate", "--edition", "11e", "--language", "en"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "logo_40k.png" in captured.err
    assert not (root / "out").exists()


def test_missing_logo_asset_raises_pdf_error_directly(tmp_path):
    root = _project_root(tmp_path)
    (root / "images" / "logo_40k.png").unlink()
    config = load_project_config(root / "project.yaml")
    paths = Paths(
        editions_root=root / "editions",
        templates_root=root / "templates",
        out_root=root / "out",
        images_root=root / "images",
    )

    with pytest.raises(PdfError, match=r"logo_40k\.png"):
        generate(config, paths, "11e", language="en")
