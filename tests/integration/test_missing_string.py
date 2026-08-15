from pathlib import Path

import pytest

from wh40k_cheatsheet.config.models import Edition, LanguageEntry, ProjectConfig
from wh40k_cheatsheet.content import ContentError
from wh40k_cheatsheet.pipeline import Paths, generate
from wh40k_cheatsheet.render import RenderError


def _paths(root: Path) -> Paths:
    return Paths(
        editions_root=root / "editions",
        templates_root=root / "templates",
        out_root=root / "out",
        images_root=root / "images",
    )


def _create_dummy_logo(root: Path) -> None:
    images_dir = root / "images"
    images_dir.mkdir(exist_ok=True)
    (images_dir / "logo_40k.png").write_bytes(b"")


def test_content_file_missing_entirely_reports_edition_revision_and_language(tmp_path):
    (tmp_path / "editions" / "10e" / "2026-01-01-00" / "en").mkdir(parents=True)
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "base.html.j2").write_text("{{ document.blocks }}")
    _create_dummy_logo(tmp_path)
    config = ProjectConfig(editions={"10e": Edition(template="base.html.j2", languages={"en": LanguageEntry()})})

    with pytest.raises(ContentError) as exc_info:
        generate(config, _paths(tmp_path), "10e", language="en")

    message = str(exc_info.value)
    assert "10e" in message
    assert "2026-01-01-00" in message
    assert "en" in message


def test_unresolved_content_reference_reports_edition_revision_and_language(tmp_path):
    content_dir = tmp_path / "editions" / "10e" / "2026-01-01-00" / "en"
    content_dir.mkdir(parents=True)
    (content_dir / "content.yaml").write_text("document:\n  blocks:\n    - type: paragraph\n")
    (tmp_path / "templates").mkdir()
    # References block.text with no default filter — undefined under StrictUndefined when absent.
    (tmp_path / "templates" / "base.html.j2").write_text("{{ document.blocks[0].text }}")
    _create_dummy_logo(tmp_path)
    config = ProjectConfig(editions={"10e": Edition(template="base.html.j2", languages={"en": LanguageEntry()})})

    with pytest.raises(RenderError) as exc_info:
        generate(config, _paths(tmp_path), "10e", language="en")

    message = str(exc_info.value)
    assert "10e" in message
    assert "2026-01-01-00" in message
    assert "en" in message
