"""Command-line entry point: argument parsing, subcommand dispatch, and top-level error handling."""

import argparse
import logging
import sys
from pathlib import Path

from wh40k_cheatsheet.config import ConfigError, load_project_config
from wh40k_cheatsheet.content import ContentError
from wh40k_cheatsheet.logging_setup import configure_logging
from wh40k_cheatsheet.pdf import PdfError
from wh40k_cheatsheet.pipeline import Paths, PipelineError, generate, list_inventory, package_all
from wh40k_cheatsheet.render import RenderError
from wh40k_cheatsheet.revision.discovery import MalformedRevisionDirectoryError, NoRevisionsError, RevisionNotFoundError
from wh40k_cheatsheet.revision.identifier import InvalidRevisionIdError, RevisionId
from wh40k_cheatsheet.versioning import (
    VersionError,
    is_valid_semver,
    parse_release_branch,
    read_project_version,
)

logger = logging.getLogger(__name__)

KNOWN_ERRORS = (
    ConfigError,
    ContentError,
    RenderError,
    PdfError,
    PipelineError,
    InvalidRevisionIdError,
    NoRevisionsError,
    RevisionNotFoundError,
    MalformedRevisionDirectoryError,
    VersionError,
)


def _default_paths(project_root: Path) -> Paths:
    """Build the standard `Paths` layout (editions/templates/out/images) rooted at a project directory.

    Args:
        project_root: The repository root containing `project.yaml`.

    Returns:
        A `Paths` pointing at that root's conventional `editions/`, `templates/`, `out/`, and
        `images/` subdirectories.
    """
    return Paths(
        editions_root=project_root / "editions",
        templates_root=project_root / "templates",
        out_root=project_root / "out",
        images_root=project_root / "images",
    )


def _cmd_generate(args: argparse.Namespace) -> int:
    """Handle the `generate` subcommand: render and write PDF(s), then print a result line per file.

    Args:
        args: Parsed CLI arguments (`project_root`, `edition`, `revision`, `language`,
            `print_friendly`).

    Returns:
        The process exit code (always `0`; failures raise instead).
    """
    project_root = Path(args.project_root)
    config = load_project_config(project_root / "project.yaml")
    paths = _default_paths(project_root)

    revision = RevisionId.parse(args.revision) if args.revision else None
    documents = generate(
        config, paths, args.edition, revision=revision, language=args.language, print_friendly=args.print_friendly
    )

    for doc in documents:
        print(f"{doc.edition_id} / {doc.revision} / {doc.language} -> {doc.pdf_path}")
        if doc.print_pdf_path is not None:
            print(f"{doc.edition_id} / {doc.revision} / {doc.language} (print-friendly) -> {doc.print_pdf_path}")
    return 0


def _cmd_package(args: argparse.Namespace) -> int:
    """Handle the `package` subcommand: build every edition/language, staged flat for release.

    Args:
        args: Parsed CLI arguments (`project_root`, `dist_dir`).

    Returns:
        The process exit code (always `0`; failures raise instead).
    """
    project_root = Path(args.project_root)
    config = load_project_config(project_root / "project.yaml")
    paths = _default_paths(project_root)

    staged = package_all(config, paths, project_root / args.dist_dir)

    for path in staged:
        print(path)
    return 0


def _cmd_validate_version(args: argparse.Namespace) -> int:
    """Handle the `validate-version` subcommand: validate a release/hotfix branch's version.

    Args:
        args: Parsed CLI arguments (`project_root`, `branch`).

    Returns:
        The process exit code (always `0`; failures raise instead).

    Raises:
        VersionError: The branch's version is malformed SemVer, or disagrees with the
            project's `pyproject.toml` version.
    """
    version = parse_release_branch(args.branch)
    if version is None:
        print(f"{args.branch}: not a release/hotfix branch, nothing to validate")
        return 0

    if not is_valid_semver(version):
        raise VersionError(f"'{args.branch}' does not contain a valid SemVer version: '{version}'")

    project_root = Path(args.project_root)
    project_version = read_project_version(project_root)
    if version != project_version:
        raise VersionError(
            f"branch '{args.branch}' declares version '{version}', but pyproject.toml declares '{project_version}'"
        )

    print(version)
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    """Handle the `list` subcommand: print every edition's languages and known revisions.

    Args:
        args: Parsed CLI arguments (`project_root`).

    Returns:
        The process exit code (always `0`; failures raise instead).
    """
    project_root = Path(args.project_root)
    config = load_project_config(project_root / "project.yaml")
    paths = _default_paths(project_root)

    inventory = list_inventory(config, paths)
    for edition_id, info in inventory.items():
        print(f"{edition_id}:")
        print(f"  languages: {', '.join(info.languages)}")
        if not info.revisions:
            print("  revisions: (none)")
            continue
        print("  revisions:")
        for revision_id in info.revisions:
            marker = " (latest)" if revision_id == info.latest else ""
            print(f"    - {revision_id}{marker}")
    return 0


def _add_verbose_flag(target: argparse.ArgumentParser, *, suppress_default: bool) -> None:
    """Register `-v`/`--verbose` on a parser, correctly composing across subparsers.

    Registered on both the top-level parser and every subparser so `-v` is accepted either
    before or after the subcommand.

    Args:
        target: The parser (top-level or a subparser) to add the flag to.
        suppress_default: When `True`, the flag's default is `argparse.SUPPRESS` instead of
            `False`, so an omitted `-v` here never overwrites a `-v` already parsed at the top
            level. argparse rebuilds a fresh namespace per subparser and merges it over the
            parent's, so a normal (non-suppressed) default would clobber the parent's `True`
            with the subparser's `False`. Pass `True` for every subparser and `False` for the
            top-level parser.
    """
    target.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=argparse.SUPPRESS if suppress_default else False,
        help="Emit DEBUG-level diagnostic detail",
    )


def build_parser() -> argparse.ArgumentParser:
    """Construct the full `wh40k-cheatsheet` argument parser, including its subcommands.

    Returns:
        The configured top-level parser, with `generate` and `list` subparsers attached.
    """
    parser = argparse.ArgumentParser(prog="wh40k-cheatsheet")
    parser.add_argument("--project-root", default=".", help="Repository root containing project.yaml")
    _add_verbose_flag(parser, suppress_default=False)
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="Generate PDF(s) for an edition")
    _add_verbose_flag(generate_parser, suppress_default=True)
    generate_parser.add_argument("--edition", required=True)
    generate_parser.add_argument("--revision", default=None, help="YYYY-MM-DD-NN; defaults to latest")
    generate_parser.add_argument("--language", default=None, help="Language code; defaults to all")
    generate_parser.add_argument(
        "--print-friendly",
        action="store_true",
        help="Also generate a black/white/grey PDF with no background watermark",
    )
    generate_parser.set_defaults(func=_cmd_generate)

    list_parser = subparsers.add_parser("list", help="List available editions, languages, and revisions")
    _add_verbose_flag(list_parser, suppress_default=True)
    list_parser.set_defaults(func=_cmd_list)

    package_parser = subparsers.add_parser(
        "package", help="Build every declared edition/language, staged flat for release"
    )
    _add_verbose_flag(package_parser, suppress_default=True)
    package_parser.add_argument(
        "--dist-dir",
        default="dist",
        help="Directory (relative to --project-root, unless absolute) staged PDFs are copied into",
    )
    package_parser.set_defaults(func=_cmd_package)

    validate_version_parser = subparsers.add_parser(
        "validate-version", help="Validate a release/hotfix branch's SemVer version against pyproject.toml"
    )
    _add_verbose_flag(validate_version_parser, suppress_default=True)
    validate_version_parser.add_argument("branch", help="Branch name, e.g. release/1.2.0 or hotfix/1.2.1")
    validate_version_parser.set_defaults(func=_cmd_validate_version)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, configure logging, and dispatch to the requested subcommand.

    Args:
        argv: Argument list to parse in place of `sys.argv[1:]`; primarily for tests.

    Returns:
        The process exit code: the subcommand's own return value, or `1` if a known error
        (`KNOWN_ERRORS`) was raised.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.verbose)
    try:
        return args.func(args)
    except KNOWN_ERRORS as exc:
        logger.critical("Error: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
