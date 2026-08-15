import shutil
from pathlib import Path

from wh40k_cheatsheet.cli import main

REPO_ROOT = Path(__file__).resolve().parents[2]


def _project_root(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    shutil.copy(REPO_ROOT / "project.yaml", root / "project.yaml")
    shutil.copytree(REPO_ROOT / "editions", root / "editions")
    shutil.copytree(REPO_ROOT / "templates", root / "templates")
    shutil.copytree(REPO_ROOT / "images", root / "images")
    return root


def _revision_id(root: Path, edition: str = "11e") -> str:
    return next((root / "editions" / edition).iterdir()).name


def test_default_generate_emits_ordered_info_stage_messages_and_preserves_stdout(tmp_path, capsys):
    root = _project_root(tmp_path)
    revision = _revision_id(root)

    exit_code = main(["--project-root", str(root), "generate", "--edition", "11e", "--language", "en"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.strip() == f"11e / {revision} / en -> {root}/out/11e/{revision}/en.pdf"

    expected_lines = [
        "INFO wh40k_cheatsheet.config.loader: configuration loaded",
        f"INFO wh40k_cheatsheet.pipeline: [11e/{revision}/en] resolving revision",
        f"INFO wh40k_cheatsheet.pipeline: [11e/{revision}/en] resolving content",
        f"INFO wh40k_cheatsheet.render.html_renderer: [11e/{revision}/en] template rendered",
        f"INFO wh40k_cheatsheet.pdf.weasyprint_pdf: [11e/{revision}/en] PDF converted",
    ]
    positions = [captured.err.index(line) for line in expected_lines]
    assert positions == sorted(positions)
    assert "DEBUG" not in captured.err


def test_default_generate_stderr_matches_across_runs(tmp_path, capsys):
    # Same default-level output must reproduce exactly across repeated runs (used as the
    # baseline that US2's verbose test compares against).
    root = _project_root(tmp_path)
    main(["--project-root", str(root), "generate", "--edition", "11e", "--language", "en"])
    first_err = capsys.readouterr().err

    shutil.rmtree(root / "out")
    main(["--project-root", str(root), "generate", "--edition", "11e", "--language", "en"])
    second_err = capsys.readouterr().err

    assert first_err == second_err


def test_verbose_adds_debug_lines_beyond_default(tmp_path, capsys):
    root = _project_root(tmp_path)
    revision = _revision_id(root)

    main(["--project-root", str(root), "generate", "--edition", "11e", "--language", "en"])
    default_err = capsys.readouterr().err

    shutil.rmtree(root / "out")
    main(["--project-root", str(root), "--verbose", "generate", "--edition", "11e", "--language", "en"])
    verbose_err = capsys.readouterr().err

    for line in default_err.splitlines():
        assert line in verbose_err
    assert "DEBUG wh40k_cheatsheet.config.loader: resolved project.yaml" in verbose_err
    assert "DEBUG wh40k_cheatsheet.content.resolver: resolved content file" in verbose_err
    assert "DEBUG wh40k_cheatsheet.render.html_renderer: resolved template name" in verbose_err
    assert (
        f"DEBUG wh40k_cheatsheet.pdf.weasyprint_pdf: output PDF path: {root}/out/11e/{revision}/en.pdf" in verbose_err
    )


def test_unknown_edition_logs_critical_and_exits_nonzero(tmp_path, capsys):
    root = _project_root(tmp_path)

    for extra_args in ([], ["--verbose"]):
        exit_code = main(["--project-root", str(root), *extra_args, "generate", "--edition", "does-not-exist"])
        captured = capsys.readouterr()
        assert exit_code == 1
        assert "CRITICAL wh40k_cheatsheet.cli: Error: edition 'does-not-exist' not found" in captured.err
        assert captured.out == ""
