"""Single place to configure logging for the whole app"""

import logging


def setup_logging(level: str = "INFO") -> None:
    """Configure the root logger; module code just uses logging.getLogger(__name__)"""
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
