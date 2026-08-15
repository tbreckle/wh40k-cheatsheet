from pathlib import Path

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


def test_generate_single_edition_language_produces_valid_html_and_pdf():
    config = load_project_config(REPO_ROOT / "project.yaml")
    paths = _paths()

    documents = generate(config, paths, "11e", language="en")

    assert len(documents) == 1
    doc = documents[0]
    assert doc.edition_id == "11e"
    assert doc.language == "en"
    assert doc.html_path.is_file()
    assert doc.pdf_path.is_file()

    html = doc.html_path.read_text(encoding="utf-8")
    assert "<html" in html.lower()

    pdf_bytes = doc.pdf_path.read_bytes()
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF-")
