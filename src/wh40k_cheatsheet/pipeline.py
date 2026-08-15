"""Orchestrates config → revision → content → HTML → PDF for one or more (edition, language) runs."""

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from wh40k_cheatsheet.config import Edition, ProjectConfig
from wh40k_cheatsheet.content import resolve_content
from wh40k_cheatsheet.pdf import PdfError, render_pdf
from wh40k_cheatsheet.render import RenderError, render_html
from wh40k_cheatsheet.revision import RevisionId, discover_revisions
from wh40k_cheatsheet.revision.discovery import Revision

logger = logging.getLogger(__name__)


class PipelineError(RuntimeError):
    """Raised when an edition, revision, or language cannot be resolved for generation."""


@dataclass(frozen=True, slots=True)
class Paths:
    """The filesystem roots the pipeline reads from and writes to.

    Attributes:
        editions_root: Directory containing per-edition/revision/language content.
        templates_root: Directory containing Jinja2 templates.
        out_root: Directory generated HTML/PDF output is written under.
        images_root: Directory containing static image assets (e.g. the page logo).
    """

    editions_root: Path
    templates_root: Path
    out_root: Path
    images_root: Path


@dataclass(frozen=True, slots=True)
class GeneratedDocument:
    """The result of generating one (edition, revision, language) document.

    Attributes:
        edition_id: The edition that was generated.
        revision: The resolved revision that was generated.
        language: The language that was generated.
        html_path: Path to the retained, intermediate HTML file.
        pdf_path: Path to the final PDF file.
        print_html_path: Path to the retained, intermediate print-friendly HTML file, or
            `None` if print-friendly generation was not requested.
        print_pdf_path: Path to the print-friendly PDF file, or `None` if print-friendly
            generation was not requested.
    """

    edition_id: str
    revision: RevisionId
    language: str
    html_path: Path
    pdf_path: Path
    print_html_path: Path | None = None
    print_pdf_path: Path | None = None


@dataclass(frozen=True, slots=True)
class EditionInventory:
    """A summary of one edition's available languages and revisions, for `list`.

    Attributes:
        languages: The edition's declared language codes, sorted.
        revisions: Every discovered revision id for this edition, in ascending order.
        latest: The most recent revision id, or `None` if the edition has no revisions.
    """

    languages: list[str]
    revisions: list[RevisionId]
    latest: RevisionId | None


def _resolve_edition(config: ProjectConfig, edition_id: str) -> Edition:
    """Look up an edition by id.

    Args:
        config: The loaded project configuration.
        edition_id: The edition id to resolve.

    Returns:
        The matching `Edition`.

    Raises:
        PipelineError: `edition_id` is not declared in `config`.
    """
    if edition_id not in config.editions:
        available = ", ".join(sorted(config.editions)) or "(none)"
        raise PipelineError(f"edition '{edition_id}' not found. Available: {available}")
    return config.editions[edition_id]


def _resolve_revision(paths: Paths, edition_id: str, requested: RevisionId | None) -> Revision:
    """Resolve an edition's revision: the latest if none was requested, else the exact match.

    Args:
        paths: Filesystem roots, used to discover available revisions.
        edition_id: The edition whose revisions are discovered.
        requested: A specific revision id to resolve, or `None` for the latest.

    Returns:
        The resolved `Revision`.

    Raises:
        NoRevisionsError: The edition has no revisions and none was requested.
        RevisionNotFoundError: `requested` does not match any discovered revision.
    """
    revision_set = discover_revisions(paths.editions_root, edition_id)
    if requested is None:
        return revision_set.latest()
    return revision_set.get(requested)


def _resolve_languages(edition: Edition, edition_id: str, requested: str | None) -> list[str]:
    """Resolve which languages to generate: every declared language, or one specific one.

    Args:
        edition: The edition whose declared languages are consulted.
        edition_id: The edition's id, used only for the error message.
        requested: A specific language code to resolve, or `None` for every declared language.

    Returns:
        The list of language codes to generate.

    Raises:
        PipelineError: `requested` is not one of `edition`'s declared languages.
    """
    if requested is None:
        return list(edition.languages)
    if requested not in edition.languages:
        available = ", ".join(sorted(edition.languages)) or "(none)"
        raise PipelineError(f"language '{requested}' not found for edition '{edition_id}'. Available: {available}")
    return [requested]


def _verify_logo_asset(paths: Paths) -> None:
    """Verify the page-header logo image exists before rendering.

    WeasyPrint itself does not fail loudly on a missing referenced image — it logs an
    internal warning and silently continues — so this check exists to make a missing logo
    a hard, visible generation failure instead (FR-005).

    Args:
        paths: Filesystem roots; `images_root` is checked for `logo_40k.png`.

    Raises:
        PdfError: The logo image is missing or not a regular file.
    """
    logo_path = paths.images_root / "logo_40k.png"
    if not logo_path.is_file():
        raise PdfError(f"logo image not found: {logo_path}")


def _render_and_write(
    paths: Paths,
    template_name: str,
    context: dict,
    *,
    out_dir: Path,
    filename_stem: str,
    stage_context: str,
) -> tuple[Path, Path]:
    """Render one context to HTML, write it, then convert and write the matching PDF.

    Args:
        paths: Filesystem roots for templates and content.
        template_name: The template to render.
        context: The Jinja2 render context (`{"document": {...}}`).
        out_dir: Directory the HTML/PDF pair is written into.
        filename_stem: Filename (without extension) shared by the HTML and PDF outputs.
        stage_context: An `"edition/revision/language"` label for log attribution.

    Returns:
        The written `(html_path, pdf_path)` pair.

    Raises:
        RenderError: Template rendering failed, e.g. an unresolved content reference; the
            (edition, revision, language) triple is prefixed onto the message here for FR-009.
    """
    try:
        html = render_html(paths.templates_root, template_name, context, stage_context=stage_context)
    except RenderError as exc:
        raise RenderError(f"[{stage_context}] {exc}") from exc

    html_path = out_dir / f"{filename_stem}.html"
    pdf_path = out_dir / f"{filename_stem}.pdf"
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html, encoding="utf-8")
    render_pdf(html, base_url=paths.templates_root, output_path=pdf_path, stage_context=stage_context)
    return html_path, pdf_path


def _generate_one(
    config: ProjectConfig,
    paths: Paths,
    edition_id: str,
    revision: Revision,
    language: str,
    *,
    print_friendly: bool = False,
) -> GeneratedDocument:
    """Render and write the HTML and PDF for one already-resolved (edition, revision, language).

    Args:
        config: The loaded project configuration.
        paths: Filesystem roots for templates, content, and output.
        edition_id: The edition being generated.
        revision: The already-resolved revision being generated.
        language: The language being generated.
        print_friendly: When `True`, additionally render and write a grayscale,
            watermark-free HTML/PDF pair alongside the standard one (FR-006/FR-007).

    Returns:
        A `GeneratedDocument` describing what was written and where.

    Raises:
        ContentError: The content file for this (edition, revision, language) is missing or
            malformed; the message already names all three (content/resolver.py).
        RenderError: Template rendering failed, e.g. an unresolved content reference; the
            (edition, revision, language) triple is prefixed onto the message here for FR-009.
    """
    stage_context = f"{edition_id}/{revision.id}/{language}"
    template_name = config.editions[edition_id].resolve_template(language)
    logger.info("[%s] resolving revision", stage_context)
    context = resolve_content(paths.editions_root, edition_id, str(revision.id), language)
    logger.info("[%s] resolving content", stage_context)

    out_dir = paths.out_root / edition_id / str(revision.id)
    html_path, pdf_path = _render_and_write(
        paths, template_name, context, out_dir=out_dir, filename_stem=language, stage_context=stage_context
    )

    print_html_path: Path | None = None
    print_pdf_path: Path | None = None
    if print_friendly:
        print_context = {**context, "document": {**context["document"], "print_friendly": True}}
        print_html_path, print_pdf_path = _render_and_write(
            paths,
            template_name,
            print_context,
            out_dir=out_dir,
            filename_stem=f"{language}-print",
            stage_context=stage_context,
        )

    return GeneratedDocument(
        edition_id=edition_id,
        revision=revision.id,
        language=language,
        html_path=html_path,
        pdf_path=pdf_path,
        print_html_path=print_html_path,
        print_pdf_path=print_pdf_path,
    )


def generate(
    config: ProjectConfig,
    paths: Paths,
    edition_id: str,
    revision: RevisionId | None = None,
    language: str | None = None,
    *,
    print_friendly: bool = False,
) -> list[GeneratedDocument]:
    """Generate HTML and PDF for one edition, across one or every declared language.

    Args:
        config: The loaded project configuration.
        paths: Filesystem roots for templates, content, and output.
        edition_id: The edition to generate.
        revision: A specific revision id to generate, or `None` for the latest.
        language: A specific language code to generate, or `None` for every declared language.
        print_friendly: When `True`, additionally generate a grayscale, watermark-free PDF
            (and its retained HTML) alongside the standard PDF for each document (FR-001).

    Returns:
        One `GeneratedDocument` per generated language, in the order generated.

    Raises:
        PdfError: The page-header logo image is missing (FR-005).
    """
    edition = _resolve_edition(config, edition_id)
    _verify_logo_asset(paths)
    resolved_revision = _resolve_revision(paths, edition_id, revision)
    languages = _resolve_languages(edition, edition_id, language)
    return [
        _generate_one(config, paths, edition_id, resolved_revision, lang, print_friendly=print_friendly)
        for lang in languages
    ]


def package_all(config: ProjectConfig, paths: Paths, dist_dir: Path) -> list[Path]:
    """Build every declared edition/language and stage the resulting PDFs flat into `dist_dir`.

    Args:
        config: The loaded project configuration.
        paths: Filesystem roots for templates, content, and output.
        dist_dir: Directory the staged PDFs are copied into, named
            `<edition_id>-<language>.pdf`; created if it doesn't already exist.

    Returns:
        The staged PDF paths, in generation order (editions in `config.list_editions()` order,
        languages in each edition's declared order).

    Raises:
        PdfError: The page-header logo image is missing (FR-005 of feature 010).
        ContentError: Any edition/language's content file is missing or malformed.
        RenderError: Template rendering failed for any edition/language.
    """
    dist_dir.mkdir(parents=True, exist_ok=True)
    staged: list[Path] = []
    for edition_id in config.list_editions():
        for doc in generate(config, paths, edition_id):
            staged_path = dist_dir / f"{doc.edition_id}-{doc.language}.pdf"
            shutil.copy2(doc.pdf_path, staged_path)
            staged.append(staged_path)
    return staged


def list_inventory(config: ProjectConfig, paths: Paths) -> dict[str, EditionInventory]:
    """Summarize every declared edition's languages and discovered revisions.

    Args:
        config: The loaded project configuration.
        paths: Filesystem roots, used to discover each edition's revisions.

    Returns:
        A mapping of edition id to its `EditionInventory`.
    """
    inventory: dict[str, EditionInventory] = {}
    for edition_id, edition in config.editions.items():
        revision_set = discover_revisions(paths.editions_root, edition_id)
        latest = revision_set.latest().id if revision_set.revisions else None
        inventory[edition_id] = EditionInventory(
            languages=sorted(edition.languages),
            revisions=revision_set.ids(),
            latest=latest,
        )
    return inventory
