"""
OAMI Enterprise
Settings Models
"""

from dataclasses import dataclass


@dataclass(slots=True)
class AppSettings:
    name: str
    version: str
    debug: bool
    timezone: str


@dataclass(slots=True)
class ServerSettings:
    host: str
    port: int


@dataclass(slots=True)
class DatabaseSettings:
    url: str


@dataclass(slots=True)
class TradingSettings:
    mode: str
    capital: int
    risk_percent: float
    max_open_positions: int


@dataclass(slots=True)
class ScannerSettings:
    enabled: bool
    interval_ms: int
    watchlist_file: str


@dataclass(slots=True)
class LoggingSettings:
    level: str
    folder: str


@dataclass(slots=True)
class Settings:
    app: AppSettings
    server: ServerSettings
    database: DatabaseSettings
    trading: TradingSettings
    scanner: ScannerSettings
    logging: LoggingSettings