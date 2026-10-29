import shutil
from pathlib import Path

import pytest

from wh40k_cheatsheet.cli import main

REPO_ROOT = Path(__file__).resolve().parents[2]

ALL_SKIP_FLAGS = (
    "--skip-core-rules",
    "--skip-core-abilities",
    "--skip-datasheet-characteristics",
    "--skip-core-stratagems",
)


def _project_root(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    shutil.copy(REPO_ROOT / "project.yaml", root / "project.yaml")
    shutil.copytree(REPO_ROOT / "editions", root / "editions")
    shutil.copytree(REPO_ROOT / "templates", root / "templates")
    return root


def test_skip_flag_writes_partial_sheet_and_prints_its_path(tmp_path, capsys):
    root = _project_root(tmp_path)

    exit_code = main(
        [
            "--project-root",
            str(root),
            "generate",
            "--edition",
            "11e",
            "--language",
            "en",
            "--skip-core-stratagems",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    lines = [line for line in captured.out.splitlines() if line.strip()]
    assert len(lines) == 1
    assert lines[0].endswith("en-no-core-stratagems.pdf")
    assert (root / "out" / "11e" / "2026-06-01-00" / "en-no-core-stratagems.pdf").is_file()


def test_generate_without_skip_flags_prints_one_line_for_full_sheet(tmp_path, capsys):
    root = _project_root(tmp_path)

    exit_code = main(["--project-root", str(root), "generate", "--edition", "11e", "--language", "en"])
    captured = capsys.readouterr()

    assert exit_code == 0
    lines = [line for line in captured.out.splitlines() if line.strip()]
    assert len(lines) == 1
    assert lines[0].endswith("en.pdf")


def test_generate_help_lists_all_four_skip_flags(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["generate", "--help"])
    captured = capsys.readouterr()

    assert exc_info.value.code == 0
    for flag in ALL_SKIP_FLAGS:
        assert flag in captured.out


def test_unknown_skip_flag_exits_2_lists_valid_flags_and_writes_nothing(tmp_path, capsys):
    root = _project_root(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        main(["--project-root", str(root), "generate", "--edition", "11e", "--skip-stratagems"])
    captured = capsys.readouterr()

    assert exc_info.value.code == 2
    for flag in ALL_SKIP_FLAGS:
        assert flag in captured.err
    assert not (root / "out").exists()


@pytest.mark.parametrize(
    "flag_order",
    [
        ["--skip-core-stratagems", "--skip-core-rules"],
        ["--skip-core-rules", "--skip-core-stratagems"],
    ],
)
def test_two_skip_flags_combine_into_one_file_regardless_of_order(tmp_path, capsys, flag_order):
    root = _project_root(tmp_path)

    exit_code = main(["--project-root", str(root), "generate", "--edition", "11e", "--language", "en", *flag_order])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.strip().endswith("en-no-core-rules-core-stratagems.pdf")
    assert (root / "out" / "11e" / "2026-06-01-00" / "en-no-core-rules-core-stratagems.pdf").is_file()


def test_all_four_skip_flags_exit_1_and_write_nothing(tmp_path, capsys):
    root = _project_root(tmp_path)

    exit_code = main(["--project-root", str(root), "generate", "--edition", "11e", *ALL_SKIP_FLAGS])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "no content" in captured.err
    assert not (root / "out").exists()


def test_non_skip_unknown_flag_keeps_the_plain_argparse_message(tmp_path, capsys):
    root = _project_root(tmp_path)

    with pytest.raises(SystemExit) as exc_info:
        main(["--project-root", str(root), "generate", "--edition", "11e", "--bogus"])
    captured = capsys.readouterr()

    assert exc_info.value.code == 2
    assert "unrecognized arguments: --bogus" in captured.err
    for flag in ALL_SKIP_FLAGS:
        assert flag not in captured.err
