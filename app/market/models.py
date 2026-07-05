"""
OAMI Enterprise
Market Models
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class MarketSnapshot:
    """
    Live Market Snapshot

    Stores both:
        • Raw market data
        • Derived market analytics
    """

    # -------------------------------------------------
    # Instrument
    # -------------------------------------------------

    symbol: str
    exchange: str = "NSE"

    # -------------------------------------------------
    # Market Data
    # -------------------------------------------------

    timestamp: Optional[int] = None

    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0

    ltp: float = 0.0

    volume: int = 0

    # -------------------------------------------------
    # Derived Values
    # -------------------------------------------------

    change: float = 0.0
    change_pct: float = 0.0

    day_range: float = 0.0
    day_range_pct: float = 0.0

    distance_from_high: float = 0.0
    distance_from_low: float = 0.0

    trend: str = "NEUTRAL"
    momentum: str = "NORMAL"

    score: int = 0
    confidence: int = 0