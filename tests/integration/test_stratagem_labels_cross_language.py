from pathlib import Path

from wh40k_cheatsheet.render.html_renderer import render_html

TEMPLATES_ROOT = Path(__file__).resolve().parents[2] / "templates"

ENGLISH_LABELS = ("WHEN:", "TARGET:", "EFFECT:", "RESTRICTIONS:")
GERMAN_LABELS = ("WANN:", "ZIEL:", "EFFEKT:", "EINSCHRÄNKUNGEN:")


def _stratagem() -> dict:
    return {
        "type": "stratagem",
        "title": "Test",
        "cost": "1CP",
        "timing": "your",
        "when": "when-body",
        "target": "target-body",
        "effect": "effect-body",
        "restrictions": "restrictions-body",
    }


def _render(language: str, i18n: dict | None) -> str:
    document = {"title": "Test", "language": language, "blocks": [_stratagem()]}
    if i18n is not None:
        document["i18n"] = i18n
    return render_html(TEMPLATES_ROOT, "cheatsheet.html.j2", {"document": document})


def test_stratagem_labels_fall_back_to_english_without_i18n():
    html = _render("en", None)
    for label in ENGLISH_LABELS:
        assert label in html


def test_stratagem_labels_use_translations_when_i18n_supplies_them():
    html = _render(
        "de",
        {
            "label_when": "WANN",
            "label_target": "ZIEL",
            "label_effect": "EFFEKT",
            "label_restrictions": "EINSCHRÄNKUNGEN",
        },
    )
    for label in GERMAN_LABELS:
        assert label in html
    for label in ENGLISH_LABELS:
        assert label not in html


def test_partial_i18n_translates_only_the_supplied_labels():
    html = _render("de", {"label_when": "WANN"})
    assert "WANN:" in html
    assert "WHEN:" not in html
    assert "TARGET:" in html
