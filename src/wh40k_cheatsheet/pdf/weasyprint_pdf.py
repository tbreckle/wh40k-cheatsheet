"""Converts rendered HTML to a PDF file on disk, using WeasyPrint."""

import logging
import time
from pathlib import Path

import weasyprint

logger = logging.getLogger(__name__)


class PdfError(RuntimeError):
    """Raised when WeasyPrint fails to convert HTML to PDF."""


def _describe_exception(exc: Exception) -> str:
    """Format an exception so the description is never blank.

    Some failures WeasyPrint raises internally (e.g. a bare `AssertionError` from its layout
    engine) carry no message, so `str(exc)` alone can be empty — leaving a `PdfError` (and the
    CLI's top-level `Error: ` line) with nothing after the colon. Prefixing the exception's
    type name guarantees a non-empty, still-useful description either way.

    Args:
        exc: The exception to describe.

    Returns:
        `"<TypeName>: <message>"`, or just `"<TypeName>"` when `exc` carries no message.
    """
    message = str(exc)
    return f"{type(exc).__name__}: {message}" if message else type(exc).__name__


def render_pdf(html: str, base_url: Path, output_path: Path, *, stage_context: str | None = None) -> None:
    """Render HTML to a PDF file, writing it atomically via a temp-file rename.

    Args:
        html: The complete HTML document to render.
        base_url: Base URL WeasyPrint resolves relative asset references against.
        output_path: Where the final PDF is written.
        stage_context: An optional `"edition/revision/language"` label included in the
            completion log line for attribution; omitted from the message when `None`.

    Raises:
        PdfError: WeasyPrint failed to render or write the PDF.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    logger.debug("converting HTML (%d bytes) to PDF at %s", len(html), output_path)
    started = time.perf_counter()
    try:
        # full_fonts=True: WeasyPrint's default font subsetting (HarfBuzz/fontTools) is
        # not run-to-run deterministic — observed byte-level differences between two
        # back-to-back generations of identical HTML. Embedding whole fonts avoids it.
        weasyprint.HTML(string=html, base_url=str(base_url)).write_pdf(str(tmp_path), full_fonts=True)
    except Exception as exc:
        tmp_path.unlink(missing_ok=True)
        logger.debug("PDF conversion failed after %.3fs", time.perf_counter() - started, exc_info=True)
        raise PdfError(f"failed to render PDF to {output_path}: {_describe_exception(exc)}") from exc
    tmp_path.replace(output_path)
    logger.debug("output PDF path: %s", output_path)
    logger.debug("PDF conversion took %.3fs", time.perf_counter() - started)
    if stage_context:
        logger.info("[%s] PDF converted", stage_context)
    else:
        logger.info("PDF converted")
