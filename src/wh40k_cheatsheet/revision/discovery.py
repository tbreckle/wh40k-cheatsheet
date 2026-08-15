"""Discovers an edition's available revisions by scanning its directory tree."""

from dataclasses import dataclass
from pathlib import Path

from wh40k_cheatsheet.revision.identifier import InvalidRevisionIdError, RevisionId


class NoRevisionsError(RuntimeError):
    """Raised when an edition has no discoverable revisions."""


class RevisionNotFoundError(RuntimeError):
    """Raised when a requested revision id doesn't match any discovered revision."""


class MalformedRevisionDirectoryError(RuntimeError):
    """Raised when a revision directory's name isn't a valid revision id."""


@dataclass(frozen=True, slots=True)
class Revision:
    """One discovered revision: its id, owning edition, and directory on disk.

    Attributes:
        id: The parsed revision id.
        edition_id: The edition this revision belongs to.
        path: The revision's directory path.
    """

    id: RevisionId
    edition_id: str
    path: Path


@dataclass(frozen=True, slots=True)
class RevisionSet:
    """Every discovered revision for one edition.

    Attributes:
        edition_id: The edition these revisions belong to.
        revisions: The discovered revisions, in ascending order.
    """

    edition_id: str
    revisions: tuple[Revision, ...]

    def latest(self) -> Revision:
        """Return the most recent revision.

        Returns:
            The `Revision` with the greatest id.

        Raises:
            NoRevisionsError: This edition has no revisions.
        """
        if not self.revisions:
            raise NoRevisionsError(f"edition '{self.edition_id}' has no revisions")
        return max(self.revisions, key=lambda r: r.id)

    def get(self, revision_id: RevisionId) -> Revision:
        """Look up a specific revision by id.

        Args:
            revision_id: The revision id to look up.

        Returns:
            The matching `Revision`.

        Raises:
            RevisionNotFoundError: No discovered revision matches `revision_id`.
        """
        for revision in self.revisions:
            if revision.id == revision_id:
                return revision
        available = ", ".join(str(r.id) for r in self.revisions) or "(none)"
        raise RevisionNotFoundError(
            f"'{revision_id}' not found for edition '{self.edition_id}'. Available: {available}"
        )

    def ids(self) -> list[RevisionId]:
        """List every discovered revision's id.

        Returns:
            The revision ids, in ascending order.
        """
        return [r.id for r in self.revisions]


def discover_revisions(editions_root: Path, edition_id: str) -> RevisionSet:
    """Scan an edition's directory for valid revision subdirectories.

    Args:
        editions_root: The root directory containing all editions.
        edition_id: The edition whose revisions are discovered.

    Returns:
        A `RevisionSet` of every valid revision directory found, sorted ascending. Empty if
        the edition directory doesn't exist or contains no subdirectories.

    Raises:
        MalformedRevisionDirectoryError: A subdirectory's name isn't a valid revision id.
    """
    edition_dir = editions_root / edition_id
    revisions: list[Revision] = []
    if edition_dir.is_dir():
        for entry in sorted(edition_dir.iterdir()):
            if not entry.is_dir():
                continue
            try:
                revision_id = RevisionId.parse(entry.name)
            except InvalidRevisionIdError as exc:
                raise MalformedRevisionDirectoryError(
                    f"edition '{edition_id}' has a malformed revision directory '{entry.name}': {exc}"
                ) from exc
            revisions.append(Revision(id=revision_id, edition_id=edition_id, path=entry))
    revisions.sort(key=lambda r: r.id)
    return RevisionSet(edition_id=edition_id, revisions=tuple(revisions))
