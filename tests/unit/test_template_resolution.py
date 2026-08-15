from wh40k_cheatsheet.config.models import Edition, LanguageEntry


def test_language_level_template_wins_over_edition_default():
    edition = Edition(
        template="base.html.j2",
        languages={"en": LanguageEntry(), "de": LanguageEntry(template="base.de.html.j2")},
    )
    assert edition.resolve_template("de") == "base.de.html.j2"


def test_falls_back_to_edition_template_when_language_has_no_override():
    edition = Edition(template="base.html.j2", languages={"en": LanguageEntry()})
    assert edition.resolve_template("en") == "base.html.j2"
