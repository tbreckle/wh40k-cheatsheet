"""Loads and validates `project.yaml` into a `ProjectConfig`."""

import logging
from pathlib import Path

import yaml
from pydantic import ValidationError

from wh40k_cheatsheet.config.models import ProjectConfig

logger = logging.getLogger(__name__)


class ConfigError(RuntimeError):
    """Raised when `project.yaml` is missing, not valid YAML, or fails schema validation."""


def load_project_config(path: Path) -> ProjectConfig:
    """Load and validate a `project.yaml` file into a `ProjectConfig`.

    Args:
        path: Path to the `project.yaml` file.

    Returns:
        The validated `ProjectConfig`.

    Raises:
        ConfigError: The file is missing, not valid YAML, not a top-level mapping, or fails
            `ProjectConfig` schema validation.
    """
    if not path.is_file():
        raise ConfigError(f"project configuration file not found: {path}")
    logger.debug("resolved project.yaml at %s", path)
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path} is not valid YAML: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigError(f"{path} must contain a mapping at the top level")
    try:
        config = ProjectConfig.model_validate(raw)
    except ValidationError as exc:
        details = "; ".join(f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in exc.errors())
        raise ConfigError(f"{path} is invalid: {details}") from exc
    logger.info("configuration loaded")
    return config
