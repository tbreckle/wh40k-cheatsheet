"""Orders a `glossary` block's terms alphabetically, independent of authored order or language."""

import unicodedata
from typing import Any


def _sort_key(term: Any) -> str:
    """Fold a glossary term into a comparable, language-agnostic sort key.

    Case-folds the term, then decomposes it (NFD) and drops Unicode combining marks, so
    accented characters sort under their base letter (`Ö` with `O`, `Ä` with `A`, `Ü` with
    `U`) and `ß` sorts as `ss` (already produced by `str.casefold()`). A missing or
    non-string term sorts first rather than raising. A single leading `[` (e.g. weapon-ability
    terms like `[ANTI-X Y+]`) is dropped first, so such terms sort under their first letter
    rather than clustering before every other term.

    Args:
        term: The glossary entry's `term` value, expected to be a `str`.

    Returns:
        The folded comparison key for `term`, or `""` if `term` is not a `str`.
    """
    if not isinstance(term, str):
        return ""
    term = term.removeprefix("[")
    folded = unicodedata.normalize("NFD", term.casefold())
    return "".join(c for c in folded if not unicodedata.combining(c))


def sort_glossary_terms(terms: list[Any]) -> list[Any]:
    """Return a glossary block's `terms` reordered into alphabetical order by `term`.

    Ordering is case-insensitive and diacritic-folded (see `_sort_key`), and depends only on
    each entry's `term`; its `text`/`html` definition never affects position. The sort is
    stable, so entries sharing an identical term keep their authored relative order.

    Args:
        terms: A glossary block's `terms` list, each entry normally a mapping with a `term`
            key, in authored order.

    Returns:
        A new list containing the same entries, reordered; `terms` itself is left unmutated.
    """
    return sorted(terms, key=lambda entry: _sort_key(entry.get("term") if isinstance(entry, dict) else None))
