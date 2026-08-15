"""Proves the quality gates themselves catch what they're configured to catch (SC-003).

Runs ruff/bandit/ty directly against the seeded `tests/fixtures/bad_example.py` (bypassing
project config where needed, since that config deliberately excludes the fixture from the
real build) and against a known-clean `src/` file, asserting each gate fires on its own
category of defect and stays silent on clean code.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BAD_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "bad_example.py"
CLEAN_FILE = REPO_ROOT / "src" / "wh40k_cheatsheet" / "logging_setup.py"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_ruff_catches_style_lint_and_mutable_default_on_bad_fixture():
    result = _run("ruff", "check", str(BAD_FIXTURE))
    assert result.returncode != 0
    assert "F401" in result.stdout
    assert "B006" in result.stdout


def test_bandit_catches_hardcoded_secret_on_bad_fixture():
    # No -c pyproject.toml: our project config excludes tests/ entirely, which would hide
    # the fixture even when its path is passed explicitly. Bandit's own defaults are enough
    # to prove the underlying detection works.
    result = _run("bandit", str(BAD_FIXTURE))
    assert "hardcoded_password_string" in result.stdout


def test_ty_catches_type_error_on_bad_fixture():
    result = _run("ty", "check", str(BAD_FIXTURE))
    assert result.returncode != 0
    assert "invalid-return-type" in result.stdout


def test_ruff_reports_no_findings_on_clean_file():
    result = _run("ruff", "check", str(CLEAN_FILE))
    assert result.returncode == 0


def test_bandit_reports_no_findings_on_clean_file():
    result = _run("bandit", str(CLEAN_FILE))
    assert "No issues identified" in result.stdout


def test_ty_reports_no_findings_on_clean_file():
    result = _run("ty", "check", str(CLEAN_FILE))
    assert result.returncode == 0
