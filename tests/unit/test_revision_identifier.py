from datetime import date

import pytest

from wh40k_cheatsheet.revision.identifier import InvalidRevisionIdError, RevisionId


def test_parse_valid_id():
    revision = RevisionId.parse("2026-08-01-00")
    assert revision.date == date(2026, 8, 1)
    assert revision.sequence == 0


def test_parse_valid_id_with_max_sequence():
    revision = RevisionId.parse("2026-08-01-99")
    assert revision.sequence == 99


def test_str_round_trips_canonical_format():
    assert str(RevisionId.parse("2026-08-01-00")) == "2026-08-01-00"


def test_missing_parts_rejected():
    with pytest.raises(InvalidRevisionIdError):
        RevisionId.parse("2026-08-01")


def test_bad_width_year_rejected():
    with pytest.raises(InvalidRevisionIdError):
        RevisionId.parse("26-08-01-00")


def test_bad_width_month_rejected():
    with pytest.raises(InvalidRevisionIdError):
        RevisionId.parse("2026-8-01-00")


def test_sequence_beyond_two_digits_rejected():
    with pytest.raises(InvalidRevisionIdError):
        RevisionId.parse("2026-08-01-100")


def test_invalid_calendar_date_rejected():
    with pytest.raises(InvalidRevisionIdError, match="calendar date"):
        RevisionId.parse("2026-13-40-00")


def test_february_30th_rejected():
    with pytest.raises(InvalidRevisionIdError, match="calendar date"):
        RevisionId.parse("2026-02-30-00")


def test_ordering_by_date():
    assert RevisionId.parse("2026-07-01-00") < RevisionId.parse("2026-08-01-00")


def test_ordering_by_sequence_within_same_date():
    assert RevisionId.parse("2026-08-01-00") < RevisionId.parse("2026-08-01-01")


def test_max_selects_latest_across_mixed_dates_and_sequences():
    ids = [
        RevisionId.parse("2026-07-01-00"),
        RevisionId.parse("2026-08-01-00"),
        RevisionId.parse("2026-08-01-01"),
    ]
    assert max(ids) == RevisionId.parse("2026-08-01-01")


def test_equal_ids_are_not_less_than_each_other():
    a = RevisionId.parse("2026-08-01-00")
    b = RevisionId.parse("2026-08-01-00")
    assert not a < b
    assert not b < a
    assert a == b
