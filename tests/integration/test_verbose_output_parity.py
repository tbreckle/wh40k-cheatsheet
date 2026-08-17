import shutil
from pathlib import Path

from tests.binary_compare import assert_bytes_equal
from wh40k_cheatsheet.cli import main

REPO_ROOT = Path(__file__).resolve().parents[2]


def _project_root(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    shutil.copy(REPO_ROOT / "project.yaml", root / "project.yaml")
    shutil.copytree(REPO_ROOT / "editions", root / "editions")
    shutil.copytree(REPO_ROOT / "templates", root / "templates")
    shutil.copytree(REPO_ROOT / "images", root / "images")
    return root


def test_html_and_pdf_bytes_identical_with_and_without_verbose(tmp_path, capsys):
    # A single shared root, not two separate copies: WeasyPrint resolves the page logo's
    # relative image reference against the absolute base_url, and that resolved absolute
    # path ends up reflected in the compressed PDF content stream — two directory copies
    # with different absolute paths would differ there for a reason unrelated to verbosity.
    root = _project_root(tmp_path)
    revision = next((root / "editions" / "11e").iterdir()).name

    main(["--project-root", str(root), "generate", "--edition", "11e", "--language", "en"])
    capsys.readouterr()
    plain_html = (root / "out" / "11e" / revision / "en.html").read_bytes()
    plain_pdf = (root / "out" / "11e" / revision / "en.pdf").read_bytes()

    main(["--project-root", str(root), "--verbose", "generate", "--edition", "11e", "--language", "en"])
    capsys.readouterr()
    verbose_html = (root / "out" / "11e" / revision / "en.html").read_bytes()
    verbose_pdf = (root / "out" / "11e" / revision / "en.pdf").read_bytes()

    assert_bytes_equal("HTML", plain_html, verbose_html)
    assert_bytes_equal("PDF", plain_pdf, verbose_pdf)
