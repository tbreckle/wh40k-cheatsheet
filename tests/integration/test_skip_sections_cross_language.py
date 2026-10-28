import shutil
from pathlib import Path

import pytest

from wh40k_cheatsheet.config import load_project_config
from wh40k_cheatsheet.pipeline import Paths, generate

REPO_ROOT = Path(__file__).resolve().parents[2]

# Section id -> (English signature, German signature), each unique to that section's region in
# the real 11e content (verified against the real rendered HTML).
SECTION_SIGNATURES = {
    "core-rules": ("1. COMMAND PHASE (08)", "1. BEFEHLSPHASE (08)"),
    "core-abilities": ("CORE ABILITIES", "KERNFÄHIGKEITEN"),
    "datasheet-characteristics": ("DATASHEET CHARACTERISTICS", "DATENBLATT-KENNWERTE"),
    "core-stratagems": ("STRATAGEMS", "GEFECHTSOPTIONEN"),
}


def _project_root(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    shutil.copy(REPO_ROOT / "project.yaml", root / "project.yaml")
    shutil.copytree(REPO_ROOT / "editions", root / "editions")
    shutil.copytree(REPO_ROOT / "templates", root / "templates")
    return root


def _paths(root: Path) -> Paths:
    return Paths(
        editions_root=root / "editions",
        templates_root=root / "templates",
        out_root=root / "out",
    )


@pytest.mark.parametrize("section_id", list(SECTION_SIGNATURES))
def test_skipping_a_section_omits_it_in_every_language(tmp_path, section_id):
    root = _project_root(tmp_path)
    config = load_project_config(root / "project.yaml")

    documents = generate(config, _paths(root), "11e", skip_sections=frozenset({section_id}))
    by_language = {doc.language: doc for doc in documents}
    assert set(by_language) == {"en", "de"}

    en_signature, de_signature = SECTION_SIGNATURES[section_id]
    en_html = by_language["en"].html_path.read_text(encoding="utf-8")
    de_html = by_language["de"].html_path.read_text(encoding="utf-8")

    assert en_signature not in en_html
    assert de_signature not in de_html

    for other_id, (other_en, other_de) in SECTION_SIGNATURES.items():
        if other_id != section_id:
            assert other_en in en_html, f"en: {other_id}'s signature missing after skipping {section_id}"
            assert other_de in de_html, f"de: {other_id}'s signature missing after skipping {section_id}"
