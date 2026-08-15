from pathlib import Path

import pytest

from wh40k_cheatsheet.versioning import (
    VersionError,
    is_prerelease,
    is_valid_semver,
    parse_release_branch,
    read_project_version,
)


@pytest.mark.parametrize(
    ("branch", "expected"),
    [
        ("release/1.2.0", "1.2.0"),
        ("hotfix/1.2.1", "1.2.1"),
        ("release/1.3.0-rc.1", "1.3.0-rc.1"),
        ("feature/x", None),
        ("develop", None),
        ("main", None),
        ("release", None),
        ("hotfix", None),
    ],
)
def test_parse_release_branch(branch, expected):
    assert parse_release_branch(branch) == expected


@pytest.mark.parametrize(
    "version",
    [
        "1.2.0",
        "0.1.0",
        "1.0.0-alpha",
        "1.0.0-alpha.1",
        "1.0.0-0.3.7",
        "1.0.0-x.7.z.92",
        "1.0.0+20130313144700",
        "1.0.0-beta+exp.sha.5114f85",
        "1.0.0-alpha+001",
    ],
)
def test_is_valid_semver_accepts_wellformed_versions(version):
    assert is_valid_semver(version)


@pytest.mark.parametrize(
    "version",
    [
        "1.2",
        "1.2.0.1",
        "01.2.0",
        "1.02.0",
        "v1.2.0",
        "1.2.0-",
        "1.2.0+",
        "",
        "release/1.2.0",
    ],
)
def test_is_valid_semver_rejects_malformed_versions(version):
    assert not is_valid_semver(version)


@pytest.mark.parametrize(
    ("version", "expected"),
    [
        ("1.0.0-alpha", True),
        ("1.0.0", False),
        ("1.0.0+build5", False),
        ("1.0.0-beta+exp.sha.5114f85", True),
    ],
)
def test_is_prerelease(version, expected):
    assert is_prerelease(version) is expected


def test_read_project_version(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "9.9.9"\n', encoding="utf-8")
    assert read_project_version(tmp_path) == "9.9.9"


def test_read_project_version_missing_file(tmp_path):
    with pytest.raises(VersionError, match=r"pyproject\.toml not found"):
        read_project_version(tmp_path)


def test_read_project_version_missing_version_field(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")
    with pytest.raises(VersionError, match=r"\[project\]\.version"):
        read_project_version(tmp_path)


def test_read_project_version_malformed_toml(tmp_path):
    (tmp_path / "pyproject.toml").write_text("not valid toml [[[", encoding="utf-8")
    with pytest.raises(VersionError, match="not valid TOML"):
        read_project_version(tmp_path)


def test_read_project_version_matches_real_pyproject_toml():
    repo_root = Path(__file__).resolve().parents[2]
    version = read_project_version(repo_root)
    assert is_valid_semver(version)
