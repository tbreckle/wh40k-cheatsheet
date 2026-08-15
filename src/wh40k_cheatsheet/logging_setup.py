"""Configures the `wh40k_cheatsheet` package logger's level and stderr handler."""

import logging
import sys

PACKAGE_LOGGER_NAME = "wh40k_cheatsheet"


def configure_logging(verbose: bool) -> None:
    """Set the package logger's threshold and attach a single stderr handler.

    Replaces any handlers already attached to the `wh40k_cheatsheet` logger, so calling this
    repeatedly (e.g. across tests in the same process) never accumulates duplicate handlers.

    Args:
        verbose: When `True`, the threshold is `DEBUG`; otherwise `INFO`.
    """
    logger = logging.getLogger(PACKAGE_LOGGER_NAME)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.propagate = False
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    logger.handlers = [handler]
