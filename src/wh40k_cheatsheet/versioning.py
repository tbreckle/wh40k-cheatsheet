"""SemVer parsing/validation for GitFlow release/hotfix branches, and reading the project's own version."""

import re
import tomllib
from pathlib import Path

# The canonical SemVer 2.0.0 regex, published at semver.org, unmodified.
SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)

_RELEASE_BRANCH_PATTERN = re.compile(r"^(?:release|hotfix)/(.+)$")

# Matches a `version = "..."` assignment line, capturing the quoted value. Anchored per-line
# (not per-file) so callers can scope it to lines already known to be inside `[project]`.
_VERSION_LINE_PATTERN = re.compile(r'^version\s*=\s*"([^"]*)"\s*$')


class VersionError(RuntimeError):
    """Raised when a release/hotfix branch's version is malformed or disagrees with `pyproject.toml`."""


def parse_release_branch(branch: str) -> str | None:
    """Extract the version portion of a `release/*` or `hotfix/*` branch name.

    Args:
        branch: A branch name, e.g. `release/1.2.0`, `hotfix/1.2.1`, or `feature/x`.

    Returns:
        The raw string after the `release/`/`hotfix/` prefix (not yet validated as SemVer), or
        `None` if `branch` doesn't start with either prefix — such branches have no version to
        validate.
    """
    match = _RELEASE_BRANCH_PATTERN.match(branch)
    return match.group(1) if match else None


def is_valid_semver(version: str) -> bool:
    """Check whether `version` is a well-formed SemVer 2.0.0 version string.

    Args:
        version: The version string to validate, e.g. `1.2.0` or `1.3.0-rc.1+build5`.

    Returns:
        `True` iff `version` fully matches the SemVer 2.0.0 grammar.
    """
    return SEMVER_PATTERN.match(version) is not None


def is_prerelease(version: str) -> bool:
    """Check whether a valid SemVer `version` carries a pre-release component.

    Args:
        version: A version string already known to satisfy `is_valid_semver`.

    Returns:
        `True` iff `version` has a non-empty pre-release component (e.g. `1.3.0-rc.1`); `False`
        for a plain or build-metadata-only version (e.g. `1.3.0`, `1.3.0+build5`).
    """
    match = SEMVER_PATTERN.match(version)
    return match is not None and match.group(4) is not None


def read_project_version(project_root: Path) -> str:
    """Read the package version declared in a project's `pyproject.toml`.

    Args:
        project_root: Directory containing `pyproject.toml`.

    Returns:
        The `[project].version` string.

    Raises:
        VersionError: `pyproject.toml` is missing, not valid TOML, or has no `[project].version`.
    """
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.is_file():
        raise VersionError(f"pyproject.toml not found: {pyproject_path}")
    try:
        with pyproject_path.open("rb") as f:
            data = tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise VersionError(f"{pyproject_path} is not valid TOML: {exc}") from exc
    try:
        return data["project"]["version"]
    except KeyError as exc:
        raise VersionError(f"{pyproject_path} has no [project].version") from exc


def write_project_version(project_root: Path, version: str) -> bool:
    """Rewrite `pyproject.toml`'s `[project].version` field in place, if it differs.

    Edits the raw text of a single `version = "..."` line inside the `[project]` table, leaving
    every other byte of the file — formatting, comments, key order, other tables' own `version`
    keys — untouched. Deliberately avoids a TOML-writing dependency: `[project].version` is
    always a simple one-line string assignment in this project's `pyproject.toml`, so a scoped
    line replacement is sufficient and keeps the diff minimal.

    Args:
        project_root: Directory containing `pyproject.toml`.
        version: The new version string to write (not validated as SemVer here — callers that
            need that guarantee, e.g. the CLI, validate before calling this).

    Returns:
        `True` if the file was rewritten (the version actually changed); `False` if the
        `[project].version` already equalled `version` (file left untouched).

    Raises:
        VersionError: `pyproject.toml` is missing, or has no `[project]` table with a
            `version = "..."` line.
    """
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.is_file():
        raise VersionError(f"pyproject.toml not found: {pyproject_path}")

    lines = pyproject_path.read_text(encoding="utf-8").splitlines(keepends=True)

    in_project_table = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_project_table = stripped == "[project]"
            continue
        if not in_project_table:
            continue
        match = _VERSION_LINE_PATTERN.match(stripped)
        if match is None:
            continue
        current = match.group(1)
        if current == version:
            return False
        lines[index] = line.replace(f'"{current}"', f'"{version}"', 1)
        pyproject_path.write_text("".join(lines), encoding="utf-8")
        return True

    raise VersionError(f"{pyproject_path} has no [project].version")
