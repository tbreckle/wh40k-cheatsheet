import shutil
from pathlib import Path

from wh40k_cheatsheet.config import load_project_config
from wh40k_cheatsheet.pipeline import Paths, generate

REPO_ROOT = Path(__file__).resolve().parents[2]


def _project_root_with_extra_revisions(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    shutil.copy(REPO_ROOT / "project.yaml", root / "project.yaml")
    shutil.copytree(REPO_ROOT / "editions", root / "editions")
    shutil.copytree(REPO_ROOT / "templates", root / "templates")
    shutil.copytree(REPO_ROOT / "images", root / "images")

    base_revision_dir = root / "editions" / "11e" / "2026-06-01-00"
    later_same_day = root / "editions" / "11e" / "2026-06-01-01"
    shutil.copytree(base_revision_dir, later_same_day)
    return root


def _paths(root: Path) -> Paths:
    return Paths(
        editions_root=root / "editions",
        templates_root=root / "templates",
        out_root=root / "out",
        images_root=root / "images",
    )


def test_default_selects_latest_revision(tmp_path):
    root = _project_root_with_extra_revisions(tmp_path)
    config = load_project_config(root / "project.yaml")

    doc = generate(config, _paths(root), "11e", language="en")[0]

    assert str(doc.revision) == "2026-06-01-01"
    assert doc.html_path == root / "out" / "11e" / "2026-06-01-01" / "en.html"
    assert doc.pdf_path == root / "out" / "11e" / "2026-06-01-01" / "en.pdf"
    assert doc.html_path.is_file()
    assert doc.pdf_path.is_file()


def test_default_selects_highest_same_day_sequence(tmp_path):
    root = _project_root_with_extra_revisions(tmp_path)
    even_later = root / "editions" / "11e" / "2026-06-01-02"
    shutil.copytree(root / "editions" / "11e" / "2026-06-01-00", even_later)
    config = load_project_config(root / "project.yaml")

    doc = generate(config, _paths(root), "11e", language="en")[0]

    assert str(doc.revision) == "2026-06-01-02"
