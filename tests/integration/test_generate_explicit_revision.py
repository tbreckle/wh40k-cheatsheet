import shutil
from pathlib import Path

from wh40k_cheatsheet.config import load_project_config
from wh40k_cheatsheet.pipeline import Paths, generate
from wh40k_cheatsheet.revision.identifier import RevisionId

REPO_ROOT = Path(__file__).resolve().parents[2]


def _project_root_with_older_and_newer_revision(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    shutil.copy(REPO_ROOT / "project.yaml", root / "project.yaml")
    shutil.copytree(REPO_ROOT / "editions", root / "editions")
    shutil.copytree(REPO_ROOT / "templates", root / "templates")
    shutil.copytree(REPO_ROOT / "images", root / "images")

    original = root / "editions" / "11e" / "2026-08-01-00"
    older = root / "editions" / "11e" / "2026-07-01-00"
    shutil.copytree(original, older)
    return root


def _paths(root: Path) -> Paths:
    return Paths(
        editions_root=root / "editions",
        templates_root=root / "templates",
        out_root=root / "out",
        images_root=root / "images",
    )


def test_explicit_revision_selects_exact_older_revision_not_latest(tmp_path):
    root = _project_root_with_older_and_newer_revision(tmp_path)
    config = load_project_config(root / "project.yaml")

    doc = generate(config, _paths(root), "11e", revision=RevisionId.parse("2026-07-01-00"), language="en")[0]

    assert str(doc.revision) == "2026-07-01-00"
    assert doc.html_path == root / "out" / "11e" / "2026-07-01-00" / "en.html"
