import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BAD_FIXTURE = REPO_ROOT / "tests" / "unit" / "fixtures" / "bad_docstring_example.py"
GOOD_FIXTURE = REPO_ROOT / "tests" / "unit" / "fixtures" / "good_docstring_example.py"

DOCSTRING_CODES = (
    "C0114",  # missing-module-docstring
    "C0115",  # missing-class-docstring
    "C0116",  # missing-function-docstring
    "W9011",  # missing-return-doc
    "W9015",  # missing-param-doc
    "W9017",  # differing-param-doc
)


def _run_pylint(*paths: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pylint", *[str(p) for p in paths]],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_bad_fixture_fails_with_expected_docstring_codes():
    result = _run_pylint(BAD_FIXTURE)
    assert result.returncode != 0
    assert "missing-function-docstring" in result.stdout
    assert "missing-param-doc" in result.stdout
    assert "differing-param-doc" in result.stdout


def test_good_fixture_has_no_docstring_findings():
    result = _run_pylint(GOOD_FIXTURE)
    for code in DOCSTRING_CODES:
        assert code not in result.stdout
