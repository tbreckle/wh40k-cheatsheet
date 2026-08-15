"""Asserts the gate configuration is a strong, explicitly enumerated, Python 3.12+ rule set (US3)."""

import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_RUFF_SELECT = {
    "E",
    "W",
    "F",
    "I",
    "N",
    "UP",
    "B",
    "A",
    "C4",
    "SIM",
    "PTH",
    "RUF",
    "S",
    "PL",
    "TID",
    "TCH",
    "PERF",
    "FURB",
    "DTZ",
    "RET",
    "ARG",
    "ERA",
    "D",
}


def _load_config() -> dict:
    return tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_ruff_select_covers_the_enumerated_strong_rule_set():
    config = _load_config()
    select = set(config["tool"]["ruff"]["lint"]["select"])
    assert select >= EXPECTED_RUFF_SELECT


def test_line_length_is_120():
    config = _load_config()
    assert config["tool"]["ruff"]["line-length"] == 120
    assert config["tool"]["pylint"]["format"]["max-line-length"] == 120


def test_python_3_12_target_consistent_across_ruff_ty_and_project():
    config = _load_config()
    assert config["tool"]["ruff"]["target-version"] == "py312"
    assert config["tool"]["pylint"]["main"]["py-version"] == "3.12"
    assert config["tool"]["ty"]["environment"]["python-version"] == "3.12"
    assert config["project"]["requires-python"] == ">=3.12"
