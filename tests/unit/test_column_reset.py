from wh40k_cheatsheet.render.html_renderer import Segment, group_by_breaks


def _block(marker: str) -> dict:
    return {"type": "paragraph", "text": marker}


def _page_break() -> dict:
    return {"type": "page_break"}


def _column_reset() -> dict:
    return {"type": "column_reset"}


def test_column_reset_marker_produces_soft_segment():
    a, b = _block("a"), _block("b")
    result = group_by_breaks([a, _column_reset(), b])
    assert result == [Segment([a], None), Segment([b], "soft")]


def test_column_reset_at_start_produces_no_leading_empty_segment():
    a = _block("a")
    result = group_by_breaks([_column_reset(), a])
    assert result == [Segment([a], "soft")]


def test_column_reset_at_end_produces_no_trailing_empty_segment():
    a = _block("a")
    result = group_by_breaks([a, _column_reset()])
    assert result == [Segment([a], None)]


def test_consecutive_column_resets_collapse_to_single_boundary():
    a, b = _block("a"), _block("b")
    result = group_by_breaks([a, _column_reset(), _column_reset(), b])
    assert result == [Segment([a], None), Segment([b], "soft")]


def test_page_break_adjacent_to_column_reset_page_wins():
    a, b = _block("a"), _block("b")
    result = group_by_breaks([a, _page_break(), _column_reset(), b])
    assert result == [Segment([a], None), Segment([b], "page")]


def test_column_reset_adjacent_to_page_break_page_wins_order_independent():
    a, b = _block("a"), _block("b")
    result = group_by_breaks([a, _column_reset(), _page_break(), b])
    assert result == [Segment([a], None), Segment([b], "page")]
