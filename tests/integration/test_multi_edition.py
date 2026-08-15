import shutil
from pathlib import Path

from wh40k_cheatsheet.config import load_project_config
from wh40k_cheatsheet.pipeline import Paths, generate, list_inventory

REPO_ROOT = Path(__file__).resolve().parents[2]

SECOND_EDITION_CONTENT = """
document:
  title: "Synthetic Second Edition"
  language: en
  blocks:
    - type: phase
      title: "SYNTHETIC-EDITION-MARKER"
"""


def _project_root_with_second_edition(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    shutil.copytree(REPO_ROOT / "editions", root / "editions")
    shutil.copytree(REPO_ROOT / "templates", root / "templates")
    shutil.copytree(REPO_ROOT / "images", root / "images")

    # Add a synthetic second edition, scoped to this temp copy only — real project.yaml/editions
    # stay untouched; this exercises multi-edition selection without fabricating permanent content.
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


def _paths(root: Path) -> Paths:
    return Paths(
        editions_root=root / "editions",
        templates_root=root / "templates",
        out_root=root / "out",
        images_root=root / "images",
    )


def test_multiple_editions_are_discoverable_and_independently_generatable(tmp_path):
    root = _project_root_with_second_edition(tmp_path)
    config = load_project_config(root / "project.yaml")
    paths = _paths(root)

    inventory = list_inventory(config, paths)
    assert set(inventory) == {"11e", "9e"}
    assert inventory["9e"].languages == ["en"]

    real_edition_doc = generate(config, paths, "11e", language="en")[0]
    synthetic_edition_doc = generate(config, paths, "9e", language="en")[0]

    real_html = real_edition_doc.html_path.read_text(encoding="utf-8")
    synthetic_html = synthetic_edition_doc.html_path.read_text(encoding="utf-8")

    assert "SYNTHETIC-EDITION-MARKER" in synthetic_html
    assert "SYNTHETIC-EDITION-MARKER" not in real_html
