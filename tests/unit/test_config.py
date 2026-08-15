import pytest

from wh40k_cheatsheet.config import ConfigError, load_project_config


def _write(tmp_path, content: str):
    path = tmp_path / "project.yaml"
    path.write_text(content, encoding="utf-8")
    return path


def test_valid_config_loads_with_template_override(tmp_path):
    path = _write(
        tmp_path,
        """
editions:
  10e:
    template: base.html.j2
    languages:
      en: {}
      de:
        template: base.de.html.j2
      it: {}
  9e:
    template: legacy.html.j2
    languages:
      en: {}
""",
    )
    config = load_project_config(path)
    assert config.list_editions() == ["10e", "9e"]
    assert config.list_languages("10e") == ["en", "de", "it"]
    assert config.editions["10e"].resolve_template("en") == "base.html.j2"
    assert config.editions["10e"].resolve_template("de") == "base.de.html.j2"


def test_missing_file_raises_config_error(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_project_config(tmp_path / "does-not-exist.yaml")


def test_invalid_yaml_raises_config_error(tmp_path):
    path = _write(tmp_path, "editions: [unterminated")
    with pytest.raises(ConfigError, match="not valid YAML"):
        load_project_config(path)


def test_non_mapping_top_level_raises_config_error(tmp_path):
    path = _write(tmp_path, "- just\n- a\n- list\n")
    with pytest.raises(ConfigError, match="mapping"):
        load_project_config(path)


def test_c1_empty_editions_rejected(tmp_path):
    path = _write(tmp_path, "editions: {}\n")
    with pytest.raises(ConfigError, match="at least one edition"):
        load_project_config(path)


def test_c1_missing_editions_key_rejected(tmp_path):
    path = _write(tmp_path, "not_editions: {}\n")
    with pytest.raises(ConfigError):
        load_project_config(path)


def test_c2_missing_template_rejected(tmp_path):
    path = _write(
        tmp_path,
        """
editions:
  10e:
    languages:
      en: {}
""",
    )
    with pytest.raises(ConfigError, match="template"):
        load_project_config(path)


def test_c3_missing_languages_key_rejected(tmp_path):
    path = _write(
        tmp_path,
        """
editions:
  10e:
    template: base.html.j2
""",
    )
    with pytest.raises(ConfigError, match="languages"):
        load_project_config(path)


def test_c3_empty_languages_rejected(tmp_path):
    path = _write(
        tmp_path,
        """
editions:
  10e:
    template: base.html.j2
    languages: {}
""",
    )
    with pytest.raises(ConfigError, match="no languages"):
        load_project_config(path)


def test_c4_invalid_language_code_rejected(tmp_path):
    path = _write(
        tmp_path,
        """
editions:
  10e:
    template: base.html.j2
    languages:
      ENGLISH: {}
""",
    )
    with pytest.raises(ConfigError, match="not a valid simple language code"):
        load_project_config(path)


def test_c5_language_template_optional(tmp_path):
    path = _write(
        tmp_path,
        """
editions:
  10e:
    template: base.html.j2
    languages:
      en: {}
""",
    )
    config = load_project_config(path)
    assert config.editions["10e"].resolve_template("en") == "base.html.j2"


def test_c6_unknown_top_level_key_rejected(tmp_path):
    path = _write(
        tmp_path,
        """
editions:
  10e:
    template: base.html.j2
    languages:
      en: {}
extra_top_level_key: true
""",
    )
    with pytest.raises(ConfigError):
        load_project_config(path)


def test_c6_unknown_edition_key_rejected(tmp_path):
    path = _write(
        tmp_path,
        """
editions:
  10e:
    template: base.html.j2
    langauges:
      en: {}
""",
    )
    with pytest.raises(ConfigError):
        load_project_config(path)


def test_c6_unknown_language_entry_key_rejected(tmp_path):
    path = _write(
        tmp_path,
        """
editions:
  10e:
    template: base.html.j2
    languages:
      en:
        typo_field: base.html.j2
""",
    )
    with pytest.raises(ConfigError):
        load_project_config(path)
