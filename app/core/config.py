"""
Configuration Service
"""

from pathlib import Path

import yaml

from app.core.settings import (
    AppSettings,
    DatabaseSettings,
    LoggingSettings,
    ScannerSettings,
    ServerSettings,
    Settings,
    TradingSettings,
)


class ConfigManager:

    def __init__(self):

        root = Path(__file__).resolve().parents[2]

        self.config_file = root / "config" / "settings.yaml"

        self.settings = self.load()

    def load(self):

        with open(self.config_file, "r", encoding="utf-8") as file:
            cfg = yaml.safe_load(file)

        return Settings(
            app=AppSettings(**cfg["app"]),
            server=ServerSettings(**cfg["server"]),
            database=DatabaseSettings(**cfg["database"]),
            trading=TradingSettings(**cfg["trading"]),
            scanner=ScannerSettings(**cfg["scanner"]),
            logging=LoggingSettings(**cfg["logging"]),
        )


config = ConfigManager()