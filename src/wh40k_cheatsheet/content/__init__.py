"""Content resolution: loading a specific (edition, revision, language)'s `content.yaml`."""

from wh40k_cheatsheet.content.resolver import ContentError, resolve_content

__all__ = ["ContentError", "resolve_content"]
