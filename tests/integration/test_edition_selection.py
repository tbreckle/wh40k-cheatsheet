from pathlib import Path

import pytest

from wh40k_cheatsheet.config import load_project_config
from wh40k_cheatsheet.pipeline import Paths, PipelineError, generate

REPO_ROOT = Path(__file__).resolve().parents[2]


def _paths() -> Paths:
    return Paths(
        editions_root=REPO_ROOT / "editions",
        templates_root=REPO_ROOT / "templates",
        out_root=REPO_ROOT / "out",
        images_root=REPO_ROOT / "images",
    )


def test_selecting_a_specific_edition_renders_that_edition_content():
    config = load_project_config(REPO_ROOT / "project.yaml")
    documents = generate(config, _paths(), "11e", language="en")

    assert documents[0].edition_id == "11e"
    html = documents[0].html_path.read_text(encoding="utf-8")
    assert "Warhammer 40" in html or "40,000" in html or "40.000" in html


def test_unknown_edition_fails_listing_available_editions():
    config = load_project_config(REPO_ROOT / "project.yaml")

    with pytest.raises(PipelineError) as exc_info:
        generate(config, _paths(), "does-not-exist")

    message = str(exc_info.value)
    assert "does-not-exist" in message
    assert "11e" in message
