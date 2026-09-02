"""HTML rendering: Jinja2 templating and page/column-break segmentation."""

from wh40k_cheatsheet.render.glossary import sort_glossary_terms
from wh40k_cheatsheet.render.html_renderer import RenderError, render_html

__all__ = ["RenderError", "render_html", "sort_glossary_terms"]
