from pathlib import Path

import pytest

from wh40k_cheatsheet.versioning import (
    VersionError,
    is_prerelease,
    is_valid_semver,
    parse_release_branch,
    read_project_version,
    write_project_version,
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


def test_write_project_version_rewrites_the_version_line(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "1.2.0"\n', encoding="utf-8")

    changed = write_project_version(tmp_path, "1.3.0")

    assert changed is True
    assert read_project_version(tmp_path) == "1.3.0"


def test_write_project_version_preserves_everything_else_in_the_file(tmp_path):
    original = (
        "# a leading comment\n"
        "[build-system]\n"
        'requires = ["hatchling"]\n\n'
        "[project]\n"
        'name = "x"  # trailing comment\n'
        'version = "1.2.0"\n'
        'description = "d"\n\n'
        "[tool.other]\n"
        'setting = "kept"\n'
    )
    (tmp_path / "pyproject.toml").write_text(original, encoding="utf-8")

    write_project_version(tmp_path, "1.3.0")

    assert (tmp_path / "pyproject.toml").read_text(encoding="utf-8") == original.replace(
        'version = "1.2.0"', 'version = "1.3.0"'
    )


def test_write_project_version_is_a_noop_when_already_matching(tmp_path):
    path = tmp_path / "pyproject.toml"
    path.write_text('[project]\nname = "x"\nversion = "1.2.0"\n', encoding="utf-8")
    mtime_before = path.stat().st_mtime_ns

    changed = write_project_version(tmp_path, "1.2.0")

    assert changed is False
    assert path.stat().st_mtime_ns == mtime_before
    assert read_project_version(tmp_path) == "1.2.0"


def test_write_project_version_ignores_a_version_key_in_another_table(tmp_path):
    # A `version = "..."` line outside `[project]` (e.g. a differently-shaped [tool.*] table)
    # must never be mistaken for the package version.
    (tmp_path / "pyproject.toml").write_text(
        '[tool.other]\nversion = "9.9.9"\n\n[project]\nname = "x"\nversion = "1.2.0"\n',
        encoding="utf-8",
    )

    write_project_version(tmp_path, "1.3.0")

    text = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "9.9.9"' in text
    assert read_project_version(tmp_path) == "1.3.0"


def test_write_project_version_missing_file(tmp_path):
    with pytest.raises(VersionError, match=r"pyproject\.toml not found"):
        write_project_version(tmp_path, "1.3.0")


def test_write_project_version_missing_project_table(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[tool.other]\nversion = "9.9.9"\n', encoding="utf-8")
    with pytest.raises(VersionError, match=r"\[project\]\.version"):
        write_project_version(tmp_path, "1.3.0")
