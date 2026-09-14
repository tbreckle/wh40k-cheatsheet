from pathlib import Path

from wh40k_cheatsheet.cli import main

REPO_ROOT = Path(__file__).resolve().parents[2]


def _project_root_with_version(tmp_path: Path, version: str) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    (root / "pyproject.toml").write_text(f'[project]\nname = "x"\nversion = "{version}"\n', encoding="utf-8")
    return root


def test_validate_version_accepts_matching_release_branch(tmp_path, capsys):
    root = _project_root_with_version(tmp_path, "1.2.0")

    exit_code = main(["--project-root", str(root), "validate-version", "release/1.2.0"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.strip() == "1.2.0"


def test_validate_version_accepts_matching_hotfix_branch(tmp_path, capsys):
    root = _project_root_with_version(tmp_path, "1.2.1")

    exit_code = main(["--project-root", str(root), "validate-version", "hotfix/1.2.1"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.strip() == "1.2.1"


def test_validate_version_is_noop_on_non_release_branch(tmp_path, capsys):
    root = _project_root_with_version(tmp_path, "1.2.0")

    exit_code = main(["--project-root", str(root), "validate-version", "feature/some-thing"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "not a release/hotfix branch" in captured.out


def test_validate_version_rejects_malformed_version(tmp_path, capsys):
    root = _project_root_with_version(tmp_path, "1.2.0")

    exit_code = main(["--project-root", str(root), "validate-version", "release/not-semver"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "release/not-semver" in captured.err
    assert "not-semver" in captured.err


def test_validate_version_rejects_mismatched_version(tmp_path, capsys):
    root = _project_root_with_version(tmp_path, "1.2.0")

    exit_code = main(["--project-root", str(root), "validate-version", "release/1.3.0"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "1.3.0" in captured.err
    assert "1.2.0" in captured.err


def test_validate_version_fix_rewrites_pyproject_toml_on_mismatch(tmp_path, capsys):
    root = _project_root_with_version(tmp_path, "1.2.0")

    exit_code = main(["--project-root", str(root), "validate-version", "release/1.3.0", "--fix"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.strip() == "1.2.0 -> 1.3.0"
    assert (root / "pyproject.toml").read_text(encoding="utf-8").splitlines()[-1] == 'version = "1.3.0"'


def test_validate_version_fix_is_a_noop_when_already_matching(tmp_path, capsys):
    root = _project_root_with_version(tmp_path, "1.2.0")
    pyproject_path = root / "pyproject.toml"
    text_before = pyproject_path.read_text(encoding="utf-8")

    exit_code = main(["--project-root", str(root), "validate-version", "release/1.2.0", "--fix"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.strip() == "1.2.0"
    assert pyproject_path.read_text(encoding="utf-8") == text_before


def test_validate_version_fix_still_rejects_malformed_version(tmp_path, capsys):
    root = _project_root_with_version(tmp_path, "1.2.0")

    exit_code = main(["--project-root", str(root), "validate-version", "release/not-semver", "--fix"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "not-semver" in captured.err
    assert (root / "pyproject.toml").read_text(encoding="utf-8").splitlines()[-1] == 'version = "1.2.0"'


def test_validate_version_fix_is_noop_on_non_release_branch(tmp_path, capsys):
    root = _project_root_with_version(tmp_path, "1.2.0")

    exit_code = main(["--project-root", str(root), "validate-version", "feature/some-thing", "--fix"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "not a release/hotfix branch" in captured.out


def test_validate_version_against_real_repo_pyproject_toml_rejects_mismatch(capsys):
    # The real repo's pyproject.toml version won't equal this arbitrarily-chosen branch version,
    # so this exercises the CLI against the actual project.yaml-adjacent file layout, not a copy.
    exit_code = main(["--project-root", str(REPO_ROOT), "validate-version", "release/999999.999999.999999"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "999999.999999.999999" in captured.err
