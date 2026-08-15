"""Reads and validates the `content.yaml` for one (edition, revision, language)."""

import logging
from pathlib import Path
from typing import Any

import yaml

CONTENT_FILENAME = "content.yaml"

logger = logging.getLogger(__name__)


class ContentError(RuntimeError):
    """Raised when a content file is missing, not valid YAML, or missing required structure."""


def resolve_content(editions_root: Path, edition_id: str, revision_id: str, language: str) -> dict[str, Any]:
    """Load and minimally validate a `content.yaml` for one (edition, revision, language).

    Args:
        editions_root: The root directory containing all editions' content.
        edition_id: The edition to resolve content for.
        revision_id: The revision to resolve content for.
        language: The language to resolve content for.

    Returns:
        The parsed content mapping, with a top-level `document.blocks` guaranteed present.

    Raises:
        ContentError: The expected `content.yaml` is missing, not valid YAML, or lacks the
            required `document`/`document.blocks` structure.
    """
    content_path = editions_root / edition_id / revision_id / language / CONTENT_FILENAME
    if not content_path.is_file():
        raise ContentError(
            f"missing content for edition '{edition_id}' revision '{revision_id}' "
            f"language '{language}': expected {content_path}"
        )
    logger.debug("resolved content file at %s", content_path)
    try:
        data = yaml.safe_load(content_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ContentError(f"{content_path} is not valid YAML: {exc}") from exc
    if not isinstance(data, dict) or "document" not in data:
        raise ContentError(f"{content_path} must contain a top-level 'document' mapping")
    document = data["document"]
    if not isinstance(document, dict) or "blocks" not in document:
        raise ContentError(f"{content_path}: 'document' must contain a 'blocks' list")
    return data
