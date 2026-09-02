"""Renders a document's blocks to HTML via Jinja2, and segments them by page/column breaks."""

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateError, select_autoescape

from wh40k_cheatsheet.render.glossary import sort_glossary_terms

logger = logging.getLogger(__name__)


class RenderError(RuntimeError):
    """Raised when Jinja2 template rendering fails."""


@dataclass(frozen=True, slots=True)
class Segment:
    """One contiguous run of content blocks destined for a single `.sheet` container.

    Attributes:
        blocks: The content blocks in this segment, in document order.
        break_type: `"page"` to force a new page before this segment, `"soft"` to realign to
            a left column without forcing a page (unless none remains), or `None` for the very
            first segment.
    """

    blocks: list[dict[str, Any]]
    break_type: Literal["page", "soft"] | None


def group_by_breaks(blocks: list[dict[str, Any]]) -> list[Segment]:
    """Split a document's blocks into segments at `page_break`/`column_reset` markers.

    Consecutive or leading/trailing markers never produce an empty segment. When a `page_break`
    and a `column_reset` are adjacent with nothing between them, `page_break` always wins.

    Args:
        blocks: The document's content blocks, in order, including any marker blocks.

    Returns:
        The blocks grouped into `Segment`s, marker blocks removed and replaced by each
        segment's `break_type`.
    """
    segments: list[Segment] = []
    current: list[dict[str, Any]] = []
    pending: Literal["page", "soft"] | None = None
    for block in blocks:
        block_type = block.get("type")
        if block_type == "page_break":
            if current:
                segments.append(Segment(current, pending))
                current = []
                pending = None
            pending = "page"
        elif block_type == "column_reset":
            if current:
                segments.append(Segment(current, pending))
                current = []
                pending = None
            if pending != "page":
                pending = "soft"
        else:
            current.append(block)
    if current:
        segments.append(Segment(current, pending))
    logger.debug(
        "grouped %d block(s) into %d segment(s) (breaks: %s)",
        len(blocks),
        len(segments),
        [s.break_type for s in segments[1:]],
    )
    return segments


def _environment(templates_root: Path) -> Environment:
    """Build the Jinja2 `Environment` used to render cheat-sheet templates.

    Args:
        templates_root: Directory Jinja2 loads template files from.

    Returns:
        A configured `Environment` with strict undefined handling, autoescaping, and
        `group_by_breaks`/`sort_glossary_terms` registered as template globals.
    """
    env = Environment(
        loader=FileSystemLoader(str(templates_root)),
        autoescape=select_autoescape(["html", "j2"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    # ty infers env.globals' value type from Jinja2's built-in defaults (range, dict, ...),
    # which is narrower than the dict's actual runtime type; assigning any callable is valid.
    env.globals["group_by_breaks"] = group_by_breaks  # ty: ignore[invalid-assignment]
    env.globals["sort_glossary_terms"] = sort_glossary_terms  # ty: ignore[invalid-assignment]
    return env


def render_html(
    templates_root: Path, template_name: str, context: dict[str, Any], *, stage_context: str | None = None
) -> str:
    """Render a named template with the given context to a complete HTML string.

    Args:
        templates_root: Directory Jinja2 loads template files from.
        template_name: The template file to render, relative to `templates_root`.
        context: The Jinja2 render context (typically `{"document": {...}}`).
        stage_context: An optional `"edition/revision/language"` label included in the
            completion log line for attribution; omitted from the message when `None`.

    Returns:
        The rendered HTML document as a string.

    Raises:
        RenderError: The template could not be found or failed to render.
    """
    env = _environment(templates_root)
    logger.debug("resolved template name: %s", template_name)
    started = time.perf_counter()
    try:
        template = env.get_template(template_name)
        html = template.render(**context)
    except TemplateError as exc:
        logger.debug("template rendering failed after %.3fs", time.perf_counter() - started, exc_info=True)
        raise RenderError(f"failed to render template '{template_name}': {exc}") from exc
    logger.debug("rendered HTML: %d bytes in %.3fs", len(html), time.perf_counter() - started)
    if stage_context:
        logger.info("[%s] template rendered", stage_context)
    else:
        logger.info("template rendered")
    return html
