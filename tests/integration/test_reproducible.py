from pathlib import Path

from tests.binary_compare import assert_bytes_equal
from wh40k_cheatsheet.config import load_project_config
from wh40k_cheatsheet.pipeline import Paths, generate

REPO_ROOT = Path(__file__).resolve().parents[2]


def _paths() -> Paths:
    return Paths(
        editions_root=REPO_ROOT / "editions",
        templates_root=REPO_ROOT / "templates",
        out_root=REPO_ROOT / "out",
        images_root=REPO_ROOT / "images",
    )


def test_regenerating_the_same_edition_language_twice_yields_identical_output():
    config = load_project_config(REPO_ROOT / "project.yaml")
    paths = _paths()

    first = generate(config, paths, "11e", language="en")[0]
    first_html = first.html_path.read_bytes()
    first_pdf = first.pdf_path.read_bytes()

    second = generate(config, paths, "11e", language="en")[0]
    second_html = second.html_path.read_bytes()
    second_pdf = second.pdf_path.read_bytes()

    assert_bytes_equal("HTML", first_html, second_html)
    assert_bytes_equal("PDF", first_pdf, second_pdf)
