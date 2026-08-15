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


def test_generate_without_language_produces_exactly_one_pdf_per_declared_language():
    config = load_project_config(REPO_ROOT / "project.yaml")
    paths = _paths()
    declared_languages = set(config.list_languages("11e"))

    documents = generate(config, paths, "11e")

    assert len(documents) == len(declared_languages)
    assert {doc.language for doc in documents} == declared_languages
    for doc in documents:
        assert doc.pdf_path.is_file()
        assert doc.pdf_path.read_bytes().startswith(b"%PDF-")
