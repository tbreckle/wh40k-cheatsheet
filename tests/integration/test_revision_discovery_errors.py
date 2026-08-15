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


def test_malformed_revision_directory_reported_on_list(tmp_path, capsys):
    root = _project_root(tmp_path)
    (root / "editions" / "11e" / "not-a-revision").mkdir()

    exit_code = main(["--project-root", str(root), "list"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "11e" in captured.err


def test_malformed_revision_directory_reported_on_generate(tmp_path, capsys):
    root = _project_root(tmp_path)
    (root / "editions" / "11e" / "not-a-revision").mkdir()

    exit_code = main(["--project-root", str(root), "generate", "--edition", "11e"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "11e" in captured.err


def test_edition_with_no_revisions_reported_on_list_as_none(tmp_path, capsys):
    root = _project_root(tmp_path)
    shutil.rmtree(root / "editions" / "11e")
    (root / "editions" / "11e").mkdir()

    exit_code = main(["--project-root", str(root), "list"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "revisions: (none)" in captured.out


def test_edition_with_no_revisions_fails_clearly_on_generate(tmp_path, capsys):
    root = _project_root(tmp_path)
    shutil.rmtree(root / "editions" / "11e")
    (root / "editions" / "11e").mkdir()

    exit_code = main(["--project-root", str(root), "generate", "--edition", "11e"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "11e" in captured.err
    assert "no revisions" in captured.err.lower()
