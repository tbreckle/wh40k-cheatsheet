"""Orchestrates config → revision → content → HTML → PDF for one or more (edition, language) runs."""

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from wh40k_cheatsheet.config import Edition, ProjectConfig
from wh40k_cheatsheet.content import ContentError, resolve_content
from wh40k_cheatsheet.content.resolver import CONTENT_FILENAME
from wh40k_cheatsheet.content.sections import (
    SECTION_IDS,
    has_content,
    has_section_markers,
    invalid_section_ids,
    omit_sections,
    output_stem,
)
from wh40k_cheatsheet.pdf import render_pdf
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
    """

    editions_root: Path
    templates_root: Path
    out_root: Path


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
        omitted_sections: Section ids actually omitted from this sheet, in canonical order;
            `()` when no `skip_sections` selection was passed or none of it applied.
    """

    edition_id: str
    revision: RevisionId
    language: str
    html_path: Path
    pdf_path: Path
    print_html_path: Path | None = None
    print_pdf_path: Path | None = None
    omitted_sections: tuple[str, ...] = ()


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


@dataclass(frozen=True, slots=True)
class _PreparedDocument:
    """One language's already-resolved, already-filtered render context, ready to write.

    Splitting "resolve + filter" (`_prepare_one`) from "render + write" (`_write_one`) is what
    lets `generate()` resolve and validate every requested language *before* writing any file
    for any of them - so a `skip_sections` selection that would empty a later language's sheet
    is caught before an earlier language's sheet is ever written (FR-011).

    Attributes:
        edition_id: The edition being generated.
        revision: The already-resolved revision being generated.
        language: The language being generated.
        template_name: The template resolved for this (edition, language).
        stage_context: An `"edition/revision/language"` label for log attribution.
        context: The Jinja2 render context, with any selected sections already omitted from
            `document.blocks`.
        omitted: The section ids actually omitted from this sheet, in canonical order.
    """

    edition_id: str
    revision: Revision
    language: str
    template_name: str
    stage_context: str
    context: dict
    omitted: tuple[str, ...]


def _prepare_one(
    config: ProjectConfig,
    paths: Paths,
    edition_id: str,
    revision: Revision,
    language: str,
    *,
    skip_sections: frozenset[str],
) -> _PreparedDocument:
    """Resolve one (edition, revision, language)'s content and apply any section omission.

    Args:
        config: The loaded project configuration.
        paths: Filesystem roots for templates, content, and output.
        edition_id: The edition being generated.
        revision: The already-resolved revision being generated.
        language: The language being generated.
        skip_sections: Section ids to omit from this sheet, if present. Already validated
            against `SECTION_IDS` by `generate()`.

    Returns:
        A `_PreparedDocument` ready to be rendered and written by `_write_one`.

    Raises:
        ContentError: The content file for this (edition, revision, language) is missing,
            malformed, or (only when `skip_sections` is non-empty) has no `section` markers to
            omit by; the message already names the content file (content/resolver.py, or here
            for the marker-less case).
        PipelineError: `skip_sections` would leave this sheet with no content at all (FR-011).
    """
    stage_context = f"{edition_id}/{revision.id}/{language}"
    template_name = config.editions[edition_id].resolve_template(language)
    logger.debug("[%s] resolved template: %s", stage_context, template_name)
    logger.info("[%s] resolving revision", stage_context)
    context = resolve_content(paths.editions_root, edition_id, str(revision.id), language)
    logger.info("[%s] resolving content", stage_context)

    blocks = context["document"]["blocks"]
    omitted: tuple[str, ...] = ()
    if skip_sections:
        if not has_section_markers(blocks):
            content_path = paths.editions_root / edition_id / str(revision.id) / language / CONTENT_FILENAME
            raise ContentError(f"{content_path}: content has no section markers; cannot skip sections")
        result = omit_sections(blocks, skip_sections)
        context = {**context, "document": {**context["document"], "blocks": result.blocks}}
        omitted = result.omitted
        if not has_content(result.blocks):
            ordered_skip = ", ".join(sid for sid in SECTION_IDS if sid in skip_sections)
            raise PipelineError(f"[{stage_context}] skipping {ordered_skip} would leave no content to generate")

    return _PreparedDocument(
        edition_id=edition_id,
        revision=revision,
        language=language,
        template_name=template_name,
        stage_context=stage_context,
        context=context,
        omitted=omitted,
    )


def _write_one(paths: Paths, prepared: _PreparedDocument, *, print_friendly: bool) -> GeneratedDocument:
    """Render and write the HTML/PDF pair(s) for one already-prepared document.

    Args:
        paths: Filesystem roots for templates, content, and output.
        prepared: The already-resolved, already-filtered document to render.
        print_friendly: When `True`, additionally render and write a grayscale
            HTML/PDF pair alongside the standard one (FR-006/FR-007).

    Returns:
        A `GeneratedDocument` describing what was written and where.

    Raises:
        RenderError: Template rendering failed, e.g. an unresolved content reference; the
            (edition, revision, language) triple is prefixed onto the message here for FR-009.
    """
    out_dir = paths.out_root / prepared.edition_id / str(prepared.revision.id)
    logger.debug("[%s] output directory: %s", prepared.stage_context, out_dir)
    html_path, pdf_path = _render_and_write(
        paths,
        prepared.template_name,
        prepared.context,
        out_dir=out_dir,
        filename_stem=output_stem(prepared.language, prepared.omitted, print_friendly=False),
        stage_context=prepared.stage_context,
    )

    print_html_path: Path | None = None
    print_pdf_path: Path | None = None
    if print_friendly:
        print_context = {**prepared.context, "document": {**prepared.context["document"], "print_friendly": True}}
        print_html_path, print_pdf_path = _render_and_write(
            paths,
            prepared.template_name,
            print_context,
            out_dir=out_dir,
            filename_stem=output_stem(prepared.language, prepared.omitted, print_friendly=True),
            stage_context=prepared.stage_context,
        )

    return GeneratedDocument(
        edition_id=prepared.edition_id,
        revision=prepared.revision.id,
        language=prepared.language,
        html_path=html_path,
        pdf_path=pdf_path,
        print_html_path=print_html_path,
        print_pdf_path=print_pdf_path,
        omitted_sections=prepared.omitted,
    )


def generate(
    config: ProjectConfig,
    paths: Paths,
    edition_id: str,
    revision: RevisionId | None = None,
    language: str | None = None,
    *,
    print_friendly: bool = False,
    skip_sections: frozenset[str] = frozenset(),
) -> list[GeneratedDocument]:
    """Generate HTML and PDF for one edition, across one or every declared language.

    Args:
        config: The loaded project configuration.
        paths: Filesystem roots for templates, content, and output.
        edition_id: The edition to generate.
        revision: A specific revision id to generate, or `None` for the latest.
        language: A specific language code to generate, or `None` for every declared language.
        print_friendly: When `True`, additionally generate a grayscale PDF
            (and its retained HTML) alongside the standard PDF for each document (FR-001).
        skip_sections: Section ids (feature 015; see `content/sections.SECTION_IDS`) to omit
            from every generated sheet. Empty (the default) leaves output byte-for-byte
            identical to before this option existed.

    Returns:
        One `GeneratedDocument` per generated language, in the order generated.

    Raises:
        PipelineError: `skip_sections` contains an id that isn't a valid section id, or would
            leave any requested language's sheet with no content (FR-011) - raised before any
            file is written for any language in this call.
    """
    invalid = invalid_section_ids(skip_sections)
    if invalid:
        raise PipelineError(f"invalid section id(s) to skip: {', '.join(invalid)}. Valid ids: {', '.join(SECTION_IDS)}")

    edition = _resolve_edition(config, edition_id)
    resolved_revision = _resolve_revision(paths, edition_id, revision)
    languages = _resolve_languages(edition, edition_id, language)
    logger.info(
        "generating edition '%s' revision '%s': %d language(s) (%s)%s%s",
        edition_id,
        resolved_revision.id,
        len(languages),
        ", ".join(languages),
        " [print-friendly]" if print_friendly else "",
        f" [skip: {', '.join(sid for sid in SECTION_IDS if sid in skip_sections)}]" if skip_sections else "",
    )
    # Resolve and filter every language FIRST (raises before writing anything if any of them
    # would end up empty), then render/write only once all of them are known to be non-empty.
    prepared_documents = [
        _prepare_one(config, paths, edition_id, resolved_revision, lang, skip_sections=skip_sections)
        for lang in languages
    ]
    return [_write_one(paths, prepared, print_friendly=print_friendly) for prepared in prepared_documents]


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
