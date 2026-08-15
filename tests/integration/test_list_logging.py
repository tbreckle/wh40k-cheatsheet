import shutil
from pathlib import Path

from wh40k_cheatsheet.cli import main
from wh40k_cheatsheet.config import load_project_config

REPO_ROOT = Path(__file__).resolve().parents[2]


def _project_root(tmp_path: Path) -> Path:
    # Scoped to exactly the 11e edition (not a wholesale copy of the real project.yaml/editions),
    # so this test's exact-output assertion stays valid regardless of how many other editions the
    # real repo happens to declare.
    root = tmp_path / "project"
    root.mkdir()
    (root / "editions").mkdir()
    shutil.copytree(REPO_ROOT / "editions" / "11e", root / "editions" / "11e")
    shutil.copytree(REPO_ROOT / "templates", root / "templates")
    shutil.copytree(REPO_ROOT / "images", root / "images")

    template = load_project_config(REPO_ROOT / "project.yaml").editions["11e"].template
    (root / "project.yaml").write_text(
        f"editions:\n  11e:\n    template: {template}\n    languages:\n      en: {{}}\n      de: {{}}\n",
        encoding="utf-8",
    )
    return root


def test_list_stdout_unchanged_by_this_feature(tmp_path, capsys):
    root = _project_root(tmp_path)
    revision = next((root / "editions" / "11e").iterdir()).name

    exit_code = main(["--project-root", str(root), "list"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == (f"11e:\n  languages: de, en\n  revisions:\n    - {revision} (latest)\n")
