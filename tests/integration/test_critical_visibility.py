import shutil
from pathlib import Path

from wh40k_cheatsheet.cli import main

REPO_ROOT = Path(__file__).resolve().parents[2]


def _project_root(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    shutil.copy(REPO_ROOT / "project.yaml", root / "project.yaml")
    shutil.copytree(REPO_ROOT / "editions", root / "editions")
    shutil.copytree(REPO_ROOT / "templates", root / "templates")
    shutil.copytree(REPO_ROOT / "images", root / "images")
    return root


def test_critical_line_distinguishable_amid_verbose_debug_volume(tmp_path, capsys):
    root = _project_root(tmp_path)

    main(["--project-root", str(root), "--verbose", "generate", "--edition", "11e", "--language", "en"])
    good_run_err = capsys.readouterr().err
    debug_line_count = sum(1 for line in good_run_err.splitlines() if line.startswith("DEBUG "))
    assert debug_line_count > 0

    exit_code = main(["--project-root", str(root), "--verbose", "generate", "--edition", "does-not-exist"])
    failing_run_err = capsys.readouterr().err

    assert exit_code == 1
    critical_lines = [line for line in failing_run_err.splitlines() if line.startswith("CRITICAL ")]
    assert len(critical_lines) == 1
    assert "edition 'does-not-exist' not found" in critical_lines[0]
