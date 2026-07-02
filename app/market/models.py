"""
OAMI Enterprise
Market Data Models
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class MarketSnapshot:
    """
    Represents the market state of a single symbol.
    """

    symbol: str

    status: str = "READY"

    ltp: Optional[float] = None

    open: Optional[float] = None

    high: Optional[float] = None

    low: Optional[float] = None

    close: Optional[float] = None

    volume: Optional[int] = None

    trend: Optional[str] = None

    score: int = 0