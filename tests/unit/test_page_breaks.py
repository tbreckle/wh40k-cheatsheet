from wh40k_cheatsheet.render.html_renderer import Segment, group_by_breaks


def _block(marker: str) -> dict:
    return {"type": "paragraph", "text": marker}


def _break() -> dict:
    return {"type": "page_break"}


def _section(section_id: str) -> dict:
    return {"type": "section", "id": section_id}


def test_no_markers_yields_single_segment():
    blocks = [_block("a"), _block("b"), _block("c")]
    assert group_by_breaks(blocks) == [Segment(blocks, None)]


def test_one_marker_mid_list_splits_into_two_segments():
    a, b, c = _block("a"), _block("b"), _block("c")
    result = group_by_breaks([a, b, _break(), c])
    assert result == [Segment([a, b], None), Segment([c], "page")]


def test_marker_at_start_produces_no_leading_empty_segment():
    a = _block("a")
    result = group_by_breaks([_break(), a])
    assert result == [Segment([a], "page")]


def test_marker_at_end_produces_no_trailing_empty_segment():
    a = _block("a")
    result = group_by_breaks([a, _break()])
    assert result == [Segment([a], None)]


def test_consecutive_markers_collapse_to_single_boundary():
    a, b = _block("a"), _block("b")
    result = group_by_breaks([a, _break(), _break(), b])
    assert result == [Segment([a], None), Segment([b], "page")]


def test_three_markers_among_four_blocks_yields_four_segments():
    a, b, c, d = _block("a"), _block("b"), _block("c"), _block("d")
    result = group_by_breaks([a, _break(), b, _break(), c, _break(), d])
    assert result == [
        Segment([a], None),
        Segment([b], "page"),
        Segment([c], "page"),
        Segment([d], "page"),
    ]


def test_empty_block_list_yields_no_segments():
    assert group_by_breaks([]) == []


def test_only_markers_yields_no_segments():
    assert group_by_breaks([_break(), _break()]) == []


def test_section_marker_between_two_blocks_does_not_split_them():
    a, b = _block("a"), _block("b")
    result = group_by_breaks([a, _section("core-rules"), b])
    assert result == [Segment([a, b], None)]


def test_leading_section_marker_produces_no_empty_segment():
    a = _block("a")
    result = group_by_breaks([_section("core-rules"), a])
    assert result == [Segment([a], None)]


def test_section_marker_does_not_change_a_break_types_segmentation():
    a = _block("a")
    with_section = group_by_breaks([_break(), _section("core-abilities"), a])
    without_section = group_by_breaks([_break(), a])
    assert with_section == without_section == [Segment([a], "page")]


def test_only_section_markers_yields_no_segments():
    assert group_by_breaks([_section("core-rules"), _section("core-abilities")]) == []


def test_no_segment_ever_contains_a_section_block():
    blocks = [_section("core-rules"), _block("a"), _break(), _section("core-abilities"), _block("b")]
    for segment in group_by_breaks(blocks):
        assert all(block.get("type") != "section" for block in segment.blocks)
