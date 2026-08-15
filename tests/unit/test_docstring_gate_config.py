import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_config() -> dict:
    return tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_ruff_selects_pydocstyle_with_google_convention():
    config = _load_config()
    assert "D" in config["tool"]["ruff"]["lint"]["select"]
    assert config["tool"]["ruff"]["lint"]["pydocstyle"]["convention"] == "google"


def test_ruff_exempts_tests_from_docstring_rules():
    config = _load_config()
    assert "D" in config["tool"]["ruff"]["lint"]["per-file-ignores"]["tests/**"]


def test_pylint_docstring_checks_are_enabled():
    config = _load_config()
    disabled = config["tool"]["pylint"]["messages control"]["disable"]
    assert "missing-module-docstring" not in disabled
    assert "missing-class-docstring" not in disabled
    assert "missing-function-docstring" not in disabled


def test_pylint_covers_private_symbols():
    config = _load_config()
    assert config["tool"]["pylint"]["basic"]["no-docstring-rgx"] == "^$"


def test_pylint_docparams_extension_enabled_and_strict():
    config = _load_config()
    assert "pylint.extensions.docparams" in config["tool"]["pylint"]["main"]["load-plugins"]
    params_doc = config["tool"]["pylint"]["parameter_documentation"]
    assert params_doc["accept-no-param-doc"] is False
    assert params_doc["accept-no-return-doc"] is False
    assert params_doc["accept-no-raise-doc"] is False
    assert params_doc["accept-no-yields-doc"] is False
    assert params_doc["default-docstring-type"] == "google"
