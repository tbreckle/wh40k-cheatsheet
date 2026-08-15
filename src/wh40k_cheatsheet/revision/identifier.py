"""The `YYYY-MM-DD-NN` revision identifier: parsing, formatting, and ordering."""

import re
from dataclasses import dataclass
from datetime import date
from functools import total_ordering

_PATTERN = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(\d{2})$")
_MAX_SEQUENCE = 99


class InvalidRevisionIdError(ValueError):
    """Raised when a string isn't a valid `YYYY-MM-DD-NN` revision id."""


@total_ordering
@dataclass(frozen=True, slots=True)
class RevisionId:
    """A revision identifier: a calendar date plus a same-day sequence number (00-99).

    Attributes:
        date: The revision's calendar date.
        sequence: The same-day sequence number, `0`-`99`.
    """

    date: date
    sequence: int

    @classmethod
    def parse(cls, raw: str) -> "RevisionId":
        """Parse a `YYYY-MM-DD-NN` string into a `RevisionId`.

        Args:
            raw: The string to parse.

        Returns:
            The parsed `RevisionId`.

        Raises:
            InvalidRevisionIdError: `raw` doesn't match the expected shape, isn't a real
                calendar date, or its sequence is outside `00`-`99`.
        """
        match = _PATTERN.match(raw)
        if match is None:
            raise InvalidRevisionIdError(f"'{raw}' is not a valid revision id (expected YYYY-MM-DD-NN)")
        year, month, day, seq = match.groups()
        try:
            revision_date = date(int(year), int(month), int(day))
        except ValueError as exc:
            raise InvalidRevisionIdError(
                f"'{raw}' is not a valid revision id: {year}-{month}-{day} is not a real calendar date"
            ) from exc
        sequence = int(seq)
        if not 0 <= sequence <= _MAX_SEQUENCE:
            raise InvalidRevisionIdError(
                f"'{raw}' is not a valid revision id: sequence {seq} must be between 00 and 99"
            )
        return cls(date=revision_date, sequence=sequence)

    def __str__(self) -> str:
        """Format back to the canonical `YYYY-MM-DD-NN` string.

        Returns:
            The `YYYY-MM-DD-NN` string representation.
        """
        return f"{self.date.isoformat()}-{self.sequence:02d}"

    def __lt__(self, other: "RevisionId") -> bool:
        """Compare by date first, then same-day sequence number.

        Args:
            other: The `RevisionId` to compare against.

        Returns:
            `True` if this id is chronologically earlier than `other`; `NotImplemented` if
            `other` isn't a `RevisionId`.
        """
        if not isinstance(other, RevisionId):
            return NotImplemented
        return (self.date, self.sequence) < (other.date, other.sequence)
