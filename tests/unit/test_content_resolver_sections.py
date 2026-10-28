from pathlib import Path

import pytest

from wh40k_cheatsheet.content import ContentError, resolve_content

EDITION = "11e"
REVISION = "2026-01-01-00"
LANGUAGE = "en"


def _write_content(tmp_path: Path, blocks_yaml: str) -> Path:
    content_dir = tmp_path / EDITION / REVISION / LANGUAGE
    content_dir.mkdir(parents=True)
    content_path = content_dir / "content.yaml"
    content_path.write_text(
        f"""
document:
  title: "Test"
  language: "{LANGUAGE}"
  blocks:
{blocks_yaml}
""",
        encoding="utf-8",
    )
    return content_path


def test_resolve_content_accepts_valid_marker_layout(tmp_path):
    _write_content(
        tmp_path,
        """    - type: section
      id: core-rules
    - type: phase
      title: "1. COMMAND PHASE"
    - type: section
      id: core-abilities
    - type: phase
      title: "Abilities"
""",
    )
    data = resolve_content(tmp_path, EDITION, REVISION, LANGUAGE)
    assert len(data["document"]["blocks"]) == 4


def test_resolve_content_accepts_zero_markers(tmp_path):
    _write_content(
        tmp_path,
        """    - type: phase
      title: "1. COMMAND PHASE"
""",
    )
    data = resolve_content(tmp_path, EDITION, REVISION, LANGUAGE)
    assert len(data["document"]["blocks"]) == 1


def test_resolve_content_rejects_duplicate_section_id(tmp_path):
    content_path = _write_content(
        tmp_path,
        """    - type: section
      id: core-rules
    - type: phase
      title: "a"
    - type: section
      id: core-rules
    - type: phase
      title: "b"
""",
    )
    with pytest.raises(ContentError) as exc_info:
        resolve_content(tmp_path, EDITION, REVISION, LANGUAGE)
    assert str(content_path) in str(exc_info.value)
    assert "core-rules" in str(exc_info.value)


def test_resolve_content_rejects_unknown_section_id(tmp_path):
    content_path = _write_content(
        tmp_path,
        """    - type: section
      id: bogus
    - type: phase
      title: "a"
""",
    )
    with pytest.raises(ContentError) as exc_info:
        resolve_content(tmp_path, EDITION, REVISION, LANGUAGE)
    assert str(content_path) in str(exc_info.value)
    assert "bogus" in str(exc_info.value)


def test_resolve_content_rejects_block_before_first_marker(tmp_path):
    content_path = _write_content(
        tmp_path,
        """    - type: phase
      title: "a"
    - type: section
      id: core-rules
    - type: phase
      title: "b"
""",
    )
    with pytest.raises(ContentError) as exc_info:
        resolve_content(tmp_path, EDITION, REVISION, LANGUAGE)
    assert str(content_path) in str(exc_info.value)
