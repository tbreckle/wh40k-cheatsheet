import shutil
from pathlib import Path

import pytest

from wh40k_cheatsheet.cli import main
from wh40k_cheatsheet.config import load_project_config
from wh40k_cheatsheet.content import ContentError
from wh40k_cheatsheet.pipeline import Paths, package_all

REPO_ROOT = Path(__file__).resolve().parents[2]

SECOND_EDITION_CONTENT = """
document:
  title: "Synthetic Second Edition"
  language: en
  blocks:
    - type: phase
      title: "SYNTHETIC-EDITION-MARKER"
"""


def _paths(root: Path = REPO_ROOT) -> Paths:
    return Paths(
        editions_root=root / "editions",
        templates_root=root / "templates",
        out_root=root / "out",
        images_root=root / "images",
    )


def _project_root(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    shutil.copy(REPO_ROOT / "project.yaml", root / "project.yaml")
    shutil.copytree(REPO_ROOT / "editions", root / "editions")
    shutil.copytree(REPO_ROOT / "templates", root / "templates")
    shutil.copytree(REPO_ROOT / "images", root / "images")
    return root


def _project_root_with_second_edition(tmp_path: Path) -> Path:
    root = _project_root(tmp_path)
    second_content_dir = root / "editions" / "9e" / "2026-01-01-00" / "en"
    second_content_dir.mkdir(parents=True)
    (second_content_dir / "content.yaml").write_text(SECOND_EDITION_CONTENT, encoding="utf-8")

    real_config = load_project_config(REPO_ROOT / "project.yaml")
    real_template = real_config.editions["11e"].template
    project_yaml = f"""
editions:
  11e:
    template: {real_template}
    languages:
      en: {{}}
      de: {{}}
  9e:
    template: {real_template}
    languages:
      en: {{}}
"""
    (root / "project.yaml").write_text(project_yaml, encoding="utf-8")
    return root


def test_package_all_stages_real_content_flat_and_named(tmp_path):
    config = load_project_config(REPO_ROOT / "project.yaml")
    staged = package_all(config, _paths(), tmp_path / "dist")

    # Subset, not exact-equality: the real project.yaml may declare more editions than just
    # 11e (that's the point of FR-002/SC-005 — new editions are picked up automatically), so
    # this only asserts 11e's own outputs are present and correctly named, not that they're
    # the only ones.
    staged_names = {p.name for p in staged}
    assert {"11e-en.pdf", "11e-de.pdf"} <= staged_names
    for path in staged:
        assert path.is_file()
        assert path.read_bytes().startswith(b"%PDF-")


def test_package_all_picks_up_a_new_edition_automatically(tmp_path):
    root = _project_root_with_second_edition(tmp_path)
    config = load_project_config(root / "project.yaml")
    staged = package_all(config, _paths(root), tmp_path / "dist")

    staged_names = {p.name for p in staged}
    assert staged_names == {"11e-en.pdf", "11e-de.pdf", "9e-en.pdf"}


def test_package_all_fails_loudly_on_broken_content(tmp_path):
    root = _project_root(tmp_path)
    (root / "editions" / "11e" / "2026-06-01-00" / "de" / "content.yaml").write_text(
        "not: valid: yaml: [[[", encoding="utf-8"
    )
    config = load_project_config(root / "project.yaml")

    with pytest.raises(ContentError):
        package_all(config, _paths(root), tmp_path / "dist")


def test_cli_package_command_writes_files_and_prints_paths(tmp_path, capsys):
    root = _project_root(tmp_path)
    dist_dir = tmp_path / "release-dist"

    exit_code = main(["--project-root", str(root), "package", "--dist-dir", str(dist_dir)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert (dist_dir / "11e-en.pdf").is_file()
    assert (dist_dir / "11e-de.pdf").is_file()
    assert str(dist_dir / "11e-en.pdf") in captured.out
    assert str(dist_dir / "11e-de.pdf") in captured.out


def test_cli_package_command_defaults_dist_dir_to_dist(tmp_path):
    root = _project_root(tmp_path)

    exit_code = main(["--project-root", str(root), "package"])

    assert exit_code == 0
    assert (root / "dist" / "11e-en.pdf").is_file()
