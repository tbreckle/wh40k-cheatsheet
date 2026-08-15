import shutil
from pathlib import Path

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


def test_nonexistent_revision_fails_listing_available(tmp_path, capsys):
    root = _project_root(tmp_path)

    exit_code = main(["--project-root", str(root), "generate", "--edition", "11e", "--revision", "2020-01-01-00"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "2020-01-01-00" in captured.err
    assert "2026-08-01-00" in captured.err
    assert not (root / "out").exists()


def test_malformed_revision_fails_with_format_message(tmp_path, capsys):
    root = _project_root(tmp_path)

    exit_code = main(["--project-root", str(root), "generate", "--edition", "11e", "--revision", "2026-13-40-00"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "calendar date" in captured.err
    assert not (root / "out").exists()
