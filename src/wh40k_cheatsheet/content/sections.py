"""Sheet-section vocabulary, marker validation, omission, and output naming.

A `content.yaml` document may declare its sheet sections with a flat structural marker block,
`{type: "section", id: "<section-id>"}` - see `SECTION_IDS` for the fixed vocabulary. A section's
region runs from its marker up to (not including) the next marker or the end of the block list.

This module never imports from `content/resolver.py` or `pipeline.py` and never raises: it returns
problems (as strings) or results for its callers to turn into `ContentError`/`PipelineError`, so it
stays a leaf dependency the resolver can safely import.
"""

from dataclasses import dataclass
from typing import Any

SECTION_MARKER_TYPE = "section"

#: The four sheet sections, in canonical (sheet) order. The single source of truth for CLI flag
#: names, content marker validation, and output file naming.
SECTION_IDS: tuple[str, ...] = (
    "core-rules",
    "core-abilities",
    "datasheet-characteristics",
    "core-stratagems",
)


@dataclass(frozen=True, slots=True)
class OmissionResult:
    """The outcome of applying a section-omission selection to a block list.

    Attributes:
        blocks: The remaining blocks, in document order.
        omitted: The section ids actually removed (present in the input AND selected), in
            canonical `SECTION_IDS` order. A selected id absent from the input is not included.
    """

    blocks: list[dict[str, Any]]
    omitted: tuple[str, ...]


def _is_section_marker(block: Any) -> bool:
    """Check whether a block is a `section` marker.

    Args:
        block: A single content block, expected to be a mapping.

    Returns:
        `True` iff `block` is a mapping whose `type` is `SECTION_MARKER_TYPE`.
    """
    return isinstance(block, dict) and block.get("type") == SECTION_MARKER_TYPE


def has_section_markers(blocks: list[dict[str, Any]]) -> bool:
    """Check whether a block list declares any sheet sections at all.

    Args:
        blocks: A document's `document.blocks` list.

    Returns:
        `True` iff at least one block is a `section` marker.
    """
    return any(_is_section_marker(block) for block in blocks)


def validate_section_markers(blocks: list[dict[str, Any]]) -> list[str]:
    """Validate a block list's `section` markers, if it has any.

    A block list with zero `section` markers is valid (synthetic/test documents keep working
    without adopting sections). Once it has at least one marker, every marker's `id` must be
    known and unique, and the very first block must itself be a marker, so every block is
    attributed to exactly one section.

    Args:
        blocks: A document's `document.blocks` list.

    Returns:
        A list of human-readable problem descriptions; empty if the markers (or their absence)
        are valid.
    """
    if not has_section_markers(blocks):
        return []

    problems: list[str] = []
    seen: set[str] = set()

    if not (blocks and _is_section_marker(blocks[0])):
        problems.append("the first block must be a 'section' marker, so no block is unattributed")

    for block in blocks:
        if not _is_section_marker(block):
            continue
        section_id = block.get("id")
        if not section_id:
            problems.append("a 'section' marker is missing its 'id' field")
            continue
        if section_id not in SECTION_IDS:
            problems.append(f"unknown section id '{section_id}' (valid ids: {', '.join(SECTION_IDS)})")
            continue
        if section_id in seen:
            problems.append(f"duplicate section id '{section_id}' (each section may appear at most once)")
            continue
        seen.add(section_id)

    return problems


def invalid_section_ids(selection: frozenset[str]) -> tuple[str, ...]:
    """Find any ids in a selection that aren't valid section ids.

    Args:
        selection: A set of section ids to validate.

    Returns:
        The invalid ids, sorted; empty if every id in `selection` is one of `SECTION_IDS`.
    """
    return tuple(sorted(section_id for section_id in selection if section_id not in SECTION_IDS))


def omit_sections(blocks: list[dict[str, Any]], selection: frozenset[str]) -> OmissionResult:
    """Remove the whole region of every selected, present section.

    A section's region is its marker plus every block up to (not including) the next marker or
    the end of the list - including any `page_break`/`column_reset` inside it. A selected section
    that has no marker in `blocks` is left untouched (it simply isn't present) and is not counted
    in the result's `omitted`. This function is pure and never raises.

    Args:
        blocks: A document's `document.blocks` list. Never mutated.
        selection: The section ids to omit, if present.

    Returns:
        An `OmissionResult` with the remaining blocks (a new list; block mappings are reused by
        reference, not copied) and the ids actually omitted, in canonical `SECTION_IDS` order.
    """
    if not selection:
        return OmissionResult(blocks=list(blocks), omitted=())

    kept: list[dict[str, Any]] = []
    actually_omitted: set[str] = set()
    dropping = False
    for block in blocks:
        if _is_section_marker(block):
            section_id = block.get("id")
            dropping = section_id in selection
            if dropping:
                actually_omitted.add(section_id)
                continue
        if dropping:
            continue
        kept.append(block)

    omitted_in_order = tuple(section_id for section_id in SECTION_IDS if section_id in actually_omitted)
    return OmissionResult(blocks=kept, omitted=omitted_in_order)


def has_content(blocks: list[dict[str, Any]]) -> bool:
    """Check whether a block list has any real (non-structural) content left.

    Args:
        blocks: A block list, typically an `OmissionResult.blocks`.

    Returns:
        `True` iff at least one block is not a `section`/`page_break`/`column_reset` marker.
    """
    structural = {SECTION_MARKER_TYPE, "page_break", "column_reset"}
    return any(not (isinstance(block, dict) and block.get("type") in structural) for block in blocks)


def output_stem(language: str, omitted: tuple[str, ...], *, print_friendly: bool) -> str:
    """Build the output filename stem (no extension) for a generated sheet.

    Args:
        language: The language code being generated.
        omitted: The section ids actually omitted from this sheet, in canonical order (typically
            an `OmissionResult.omitted`).
        print_friendly: Whether this is the print-friendly variant of the sheet.

    Returns:
        `language`, with `-no-<ids joined by ->` appended when `omitted` is non-empty, and
        `-print` appended when `print_friendly` is `True`.
    """
    stem = language
    if omitted:
        stem += "-no-" + "-".join(omitted)
    if print_friendly:
        stem += "-print"
    return stem
