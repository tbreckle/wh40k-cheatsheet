from pathlib import Path

from wh40k_cheatsheet.content import resolve_content
from wh40k_cheatsheet.content.sections import (
    SECTION_IDS,
    has_content,
    has_section_markers,
    invalid_section_ids,
    omit_sections,
    output_stem,
    validate_section_markers,
)
from wh40k_cheatsheet.render.html_renderer import group_by_breaks

REPO_ROOT = Path(__file__).resolve().parents[2]


def _section(section_id: str) -> dict:
    return {"type": "section", "id": section_id}


def _phase(title: str) -> dict:
    return {"type": "phase", "title": title}


def _break() -> dict:
    return {"type": "page_break"}


def _reset() -> dict:
    return {"type": "column_reset"}


def test_section_ids_is_the_canonical_four_in_sheet_order():
    assert SECTION_IDS == ("core-rules", "core-abilities", "datasheet-characteristics", "core-stratagems")


def test_validate_section_markers_accepts_a_valid_document():
    blocks = [_section("core-rules"), _phase("a"), _section("core-abilities"), _phase("b")]
    assert validate_section_markers(blocks) == []


def test_validate_section_markers_accepts_zero_markers():
    assert validate_section_markers([_phase("a"), _phase("b")]) == []
    assert validate_section_markers([]) == []


def test_validate_section_markers_rejects_unknown_id():
    problems = validate_section_markers([_section("bogus"), _phase("a")])
    assert problems
    assert any("bogus" in p for p in problems)


def test_validate_section_markers_rejects_missing_id():
    problems = validate_section_markers([{"type": "section"}, _phase("a")])
    assert problems


def test_validate_section_markers_rejects_duplicate_id():
    problems = validate_section_markers([_section("core-rules"), _phase("a"), _section("core-rules"), _phase("b")])
    assert problems
    assert any("core-rules" in p for p in problems)


def test_validate_section_markers_rejects_block_before_first_marker():
    problems = validate_section_markers([_phase("a"), _section("core-rules"), _phase("b")])
    assert problems


def test_has_section_markers():
    assert has_section_markers([_section("core-rules"), _phase("a")]) is True
    assert has_section_markers([_phase("a")]) is False
    assert has_section_markers([]) is False


def test_invalid_section_ids():
    assert invalid_section_ids(frozenset()) == ()
    assert invalid_section_ids(frozenset({"core-rules"})) == ()
    assert invalid_section_ids(frozenset({"core-rules", "bogus"})) == ("bogus",)
    assert invalid_section_ids(frozenset({"zzz", "aaa"})) == ("aaa", "zzz")


# --- omit_sections ---


def _full_document() -> list[dict]:
    return [
        _section("core-rules"),
        _phase("Command Phase"),
        _section("core-abilities"),
        _break(),
        _reset(),
        _phase("Core Abilities Glossary"),
        _section("datasheet-characteristics"),
        _phase("Datasheet Characteristics Glossary"),
        _section("core-stratagems"),
        _break(),
        _phase("Stratagems"),
    ]


def test_omit_sections_empty_selection_returns_blocks_unchanged():
    blocks = _full_document()
    result = omit_sections(blocks, frozenset())
    assert result.blocks == blocks
    assert result.omitted == ()


def test_omit_sections_removes_whole_region_including_marker_and_its_breaks():
    blocks = _full_document()
    result = omit_sections(blocks, frozenset({"core-stratagems"}))
    assert result.omitted == ("core-stratagems",)
    assert _section("core-stratagems") not in result.blocks
    assert _break() not in result.blocks[-2:]
    assert _phase("Stratagems") not in result.blocks
    # everything else survives
    assert _phase("Command Phase") in result.blocks
    assert _phase("Datasheet Characteristics Glossary") in result.blocks


def test_omit_sections_absent_section_removes_nothing():
    # 10e-shaped document: no datasheet-characteristics marker at all.
    blocks = [
        _section("core-rules"),
        _phase("a"),
        _section("core-abilities"),
        _phase("b"),
        _section("core-stratagems"),
        _phase("c"),
    ]
    result = omit_sections(blocks, frozenset({"datasheet-characteristics"}))
    assert result.blocks == blocks
    assert result.omitted == ()


def test_omit_sections_two_selected_yield_canonical_order_regardless_of_set_order():
    blocks = _full_document()
    r1 = omit_sections(blocks, frozenset({"core-stratagems", "core-rules"}))
    r2 = omit_sections(blocks, frozenset({"core-rules", "core-stratagems"}))
    assert r1.omitted == r2.omitted == ("core-rules", "core-stratagems")
    assert r1.blocks == r2.blocks


def test_omit_sections_unselected_sections_keep_their_marker():
    blocks = _full_document()
    result = omit_sections(blocks, frozenset({"core-stratagems"}))
    assert _section("core-rules") in result.blocks
    assert _section("core-abilities") in result.blocks
    assert _section("datasheet-characteristics") in result.blocks


def test_omit_sections_does_not_mutate_input():
    blocks = _full_document()
    original = list(blocks)
    original_ids = [id(b) for b in blocks]
    omit_sections(blocks, frozenset({"core-abilities"}))
    assert blocks == original
    assert [id(b) for b in blocks] == original_ids


# --- has_content ---


def test_has_content_false_for_empty_list():
    assert has_content([]) is False


def test_has_content_false_for_only_structural_blocks():
    assert has_content([_section("core-rules"), _break(), _reset()]) is False


def test_has_content_true_when_a_real_block_present():
    assert has_content([_section("core-rules"), _phase("a")]) is True


# --- output_stem ---


def test_output_stem_no_omission_no_print_friendly():
    assert output_stem("en", (), print_friendly=False) == "en"


def test_output_stem_no_omission_print_friendly():
    assert output_stem("en", (), print_friendly=True) == "en-print"


def test_output_stem_single_omission():
    assert output_stem("en", ("core-stratagems",), print_friendly=False) == "en-no-core-stratagems"


def test_output_stem_multiple_omissions_print_friendly():
    assert (
        output_stem("en", ("core-rules", "core-stratagems"), print_friendly=True)
        == "en-no-core-rules-core-stratagems-print"
    )


def test_output_stem_de_no_omission():
    assert output_stem("de", (), print_friendly=False) == "de"


# --- combinatorial: no empty columns for any selection, against real shipped content ---


def _shipped_documents() -> list[tuple[str, list[dict]]]:
    latest = {"11e": "2026-06-01-00"}
    triples = [("11e", "en"), ("11e", "de")]
    documents = []
    for edition_id, language in triples:
        content = resolve_content(REPO_ROOT / "editions", edition_id, latest[edition_id], language)
        documents.append((f"{edition_id}/{language}", content["document"]["blocks"]))
    return documents


def _all_nonempty_subsets(items: tuple[str, ...]):
    n = len(items)
    for mask in range(1, 2**n):
        yield frozenset(items[i] for i in range(n) if mask & (1 << i))


def test_omitting_any_combination_never_leaves_an_empty_segment():
    for label, blocks in _shipped_documents():
        full_segment_count = len(group_by_breaks(blocks))
        for selection in _all_nonempty_subsets(SECTION_IDS):
            result = omit_sections(blocks, selection)
            if not has_content(result.blocks):
                continue
            segments = group_by_breaks(result.blocks)
            for segment in segments:
                assert segment.blocks, (
                    f"{label}: empty segment after omitting {sorted(selection)} (break_type={segment.break_type})"
                )
            assert len(segments) <= full_segment_count, (
                f"{label}: omitting {sorted(selection)} produced more segments ({len(segments)}) "
                f"than the full sheet ({full_segment_count})"
            )
