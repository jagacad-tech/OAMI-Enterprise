"""
Central Logging Service
"""

from pathlib import Path
import logging

from app.core.constants import (
    DEFAULT_LOG_FORMAT,
    SYSTEM_LOGGER,
)


class LogManager:

    def __init__(self):

        log_dir = Path("logs")

        log_dir.mkdir(exist_ok=True)

        self.logger = logging.getLogger(SYSTEM_LOGGER)

        self.logger.setLevel(logging.INFO)

        if self.logger.handlers:
            return

        formatter = logging.Formatter(DEFAULT_LOG_FORMAT)

        console = logging.StreamHandler()

        console.setFormatter(formatter)

        file_handler = logging.FileHandler(
            log_dir / "oami.log",
            encoding="utf-8",
        )

        file_handler.setFormatter(formatter)

        self.logger.addHandler(console)

        self.logger.addHandler(file_handler)

    def get_logger(self):

        return self.logger


logger = LogManager().get_logger()