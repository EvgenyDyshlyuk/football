"""Central logging configuration for the application."""

from __future__ import annotations

import logging
import os


def configure_logging() -> None:
    """Configure the root logger.

    The log level can be controlled via the ``LOG_LEVEL`` environment variable
    and currently supports ``INFO`` and ``DEBUG``. Any other value defaults to
    ``INFO``.
    """

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    if level_name not in {"INFO", "DEBUG"}:
        level_name = "INFO"

    logging.basicConfig(
        level=getattr(logging, level_name, logging.INFO),
        format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    )
