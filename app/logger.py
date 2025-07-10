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

    level_name = os.getenv("LOG_LEVEL")
    if level_name:
        level = getattr(logging, level_name.upper(), logging.INFO)
    else:
        level = logging.INFO
        for name in ("gunicorn.error", "uvicorn.error"):
            logger = logging.getLogger(name)
            if logger.level:
                level = logger.level
                break

    root_logger = logging.getLogger()
    if root_logger.handlers:
        root_logger.setLevel(level)
    else:
        logging.basicConfig(level=level, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s")
