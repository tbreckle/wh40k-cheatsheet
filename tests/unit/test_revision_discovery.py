import pytest

from wh40k_cheatsheet.revision.discovery import (
    MalformedRevisionDirectoryError,
    NoRevisionsError,
    RevisionNotFoundError,
    discover_revisions,
)
from wh40k_cheatsheet.revision.identifier import RevisionId


def _make_revision_dirs(editions_root, edition_id: str, names: list[str]) -> None:
    for name in names:
        (editions_root / edition_id / name).mkdir(parents=True)


def test_discovers_and_orders_revisions_chronologically(tmp_path):
    _make_revision_dirs(tmp_path, "10e", ["2026-08-01-00", "2026-07-01-00", "2026-08-01-01"])

    revision_set = discover_revisions(tmp_path, "10e")

    assert [str(r.id) for r in revision_set.revisions] == [
        "2026-07-01-00",
        "2026-08-01-00",
        "2026-08-01-01",
    ]


def test_latest_selects_highest_sequence_on_the_same_day(tmp_path):
    _make_revision_dirs(tmp_path, "10e", ["2026-08-01-00", "2026-08-01-01"])

    revision_set = discover_revisions(tmp_path, "10e")

    assert str(revision_set.latest().id) == "2026-08-01-01"


def test_latest_with_single_revision(tmp_path):
    _make_revision_dirs(tmp_path, "10e", ["2026-08-01-00"])

    revision_set = discover_revisions(tmp_path, "10e")

    assert str(revision_set.latest().id) == "2026-08-01-00"


def test_get_returns_exact_requested_revision(tmp_path):
    _make_revision_dirs(tmp_path, "10e", ["2026-07-01-00", "2026-08-01-00"])
    revision_set = discover_revisions(tmp_path, "10e")

    found = revision_set.get(RevisionId.parse("2026-07-01-00"))

    assert str(found.id) == "2026-07-01-00"


def test_get_unknown_revision_lists_available(tmp_path):
    _make_revision_dirs(tmp_path, "10e", ["2026-08-01-00"])
    revision_set = discover_revisions(tmp_path, "10e")

    with pytest.raises(RevisionNotFoundError, match="2026-08-01-00"):
        revision_set.get(RevisionId.parse("2020-01-01-00"))


def test_malformed_revision_directory_name_is_reported(tmp_path):
    _make_revision_dirs(tmp_path, "10e", ["not-a-revision"])

    with pytest.raises(MalformedRevisionDirectoryError, match="10e"):
        discover_revisions(tmp_path, "10e")


def test_empty_revision_set_raises_on_latest(tmp_path):
    (tmp_path / "10e").mkdir()

    revision_set = discover_revisions(tmp_path, "10e")

    with pytest.raises(NoRevisionsError, match="10e"):
        revision_set.latest()


def test_missing_edition_directory_yields_empty_set(tmp_path):
    revision_set = discover_revisions(tmp_path, "does-not-exist")

    assert revision_set.revisions == ()
    with pytest.raises(NoRevisionsError):
        revision_set.latest()


def test_non_directory_entries_are_ignored(tmp_path):
    (tmp_path / "10e").mkdir(parents=True)
    (tmp_path / "10e" / "2026-08-01-00").mkdir()
    (tmp_path / "10e" / "README.md").write_text("not a revision dir")

    revision_set = discover_revisions(tmp_path, "10e")

    assert [str(r.id) for r in revision_set.revisions] == ["2026-08-01-00"]
