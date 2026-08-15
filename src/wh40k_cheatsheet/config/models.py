"""Pydantic schema for `project.yaml`: editions, their languages, and template resolution."""

import re

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

_LANG_CODE_PATTERN = re.compile(r"^[a-z]{2}(-[A-Za-z0-9]+)?$")


class LanguageEntry(BaseModel):
    """One language declared under an edition, with an optional per-language template override.

    Attributes:
        template: A template filename overriding the edition's default for this language, or
            `None` to use the edition's own `template`.
    """

    model_config = ConfigDict(extra="forbid")

    template: str | None = None


class Edition(BaseModel):
    """One edition's default template and its declared languages.

    Attributes:
        template: The default template filename used unless a language overrides it.
        languages: Mapping of simple language code (e.g. `en`, `de`) to its `LanguageEntry`.
    """

    model_config = ConfigDict(extra="forbid")

    template: str
    languages: dict[str, LanguageEntry]

    @field_validator("languages")
    @classmethod
    def _languages_non_empty(cls, value: dict[str, LanguageEntry]) -> dict[str, LanguageEntry]:
        """Reject an edition with no languages, or with a malformed language code.

        Args:
            value: The `languages` mapping as parsed from YAML.

        Returns:
            `value`, unchanged, once validated.

        Raises:
            ValueError: `value` is empty, or a key is not a valid simple language code.
        """
        if not value:
            raise ValueError("edition has no languages")
        for code in value:
            if not _LANG_CODE_PATTERN.match(code):
                raise ValueError(f"'{code}' is not a valid simple language code")
        return value

    def resolve_template(self, language: str) -> str:
        """Resolve the template filename to use for one of this edition's languages.

        Args:
            language: The language code to resolve a template for.

        Returns:
            That language's `LanguageEntry.template` override if set, otherwise the edition's
            own default `template`.
        """
        entry = self.languages.get(language)
        if entry is not None and entry.template is not None:
            return entry.template
        return self.template


class ProjectConfig(BaseModel):
    """The top-level `project.yaml` schema: every declared edition, keyed by edition id.

    Attributes:
        editions: Mapping of edition id (e.g. `11e`) to its `Edition`.
    """

    model_config = ConfigDict(extra="forbid")

    editions: dict[str, Edition]

    @model_validator(mode="after")
    def _editions_non_empty(self) -> "ProjectConfig":
        """Reject a configuration that declares no editions at all.

        Returns:
            `self`, unchanged, once validated.

        Raises:
            ValueError: `editions` is empty.
        """
        if not self.editions:
            raise ValueError("'editions' must declare at least one edition")
        return self

    def list_editions(self) -> list[str]:
        """List every declared edition id.

        Returns:
            The edition ids, in declaration order.
        """
        return list(self.editions)

    def list_languages(self, edition_id: str) -> list[str]:
        """List the declared language codes for one edition.

        Args:
            edition_id: The edition to list languages for.

        Returns:
            That edition's language codes, in declaration order.
        """
        return list(self.editions[edition_id].languages)
