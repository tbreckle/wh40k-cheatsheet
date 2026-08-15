from wh40k_cheatsheet.render.html_renderer import Segment, group_by_breaks


def _block(marker: str) -> dict:
    return {"type": "paragraph", "text": marker}


def _break() -> dict:
    return {"type": "page_break"}


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
