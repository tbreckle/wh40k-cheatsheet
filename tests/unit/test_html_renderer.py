from pathlib import Path

from wh40k_cheatsheet.render.html_renderer import render_html

TEMPLATES_ROOT = Path(__file__).resolve().parent / "fixtures"
GOLDEN_FILE = Path(__file__).resolve().parents[1] / "golden" / "basic_render.html"

FIXED_CONTEXT = {
    "title": "Test Title",
    "escaped_text": "<script>alert('xss')</script>",
    "trusted_html": "<b>bold</b>",
    "items": ["one", "two"],
}


def _render() -> str:
    return render_html(TEMPLATES_ROOT, "golden_template.html.j2", FIXED_CONTEXT)


def test_render_matches_golden_snapshot():
    html = _render()
    expected = GOLDEN_FILE.read_text(encoding="utf-8")
    assert html == expected


def test_plain_text_is_autoescaped():
    html = _render()
    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html


def test_safe_filtered_html_is_injected_unescaped():
    html = _render()
    assert "<b>bold</b>" in html


def test_loop_renders_every_item_in_order():
    html = _render()
    assert html.index("one") < html.index("two")
