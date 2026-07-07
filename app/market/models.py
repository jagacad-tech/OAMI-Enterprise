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

    Stores:
    - Raw market data
    - Derived analytics
    - Trading intelligence
    """

    # =====================================================
    # Instrument
    # =====================================================

    symbol: str
    exchange: str = "NSE"

    # =====================================================
    # Raw Market Data
    # =====================================================

    timestamp: Optional[int] = None

    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0

    ltp: float = 0.0

    volume: int = 0

    # =====================================================
    # Derived Price Analytics
    # =====================================================

    change: float = 0.0
    change_pct: float = 0.0

    rvol: float = 0.0

    day_range: float = 0.0
    day_range_pct: float = 0.0

    distance_from_high: float = 0.0
    distance_from_low: float = 0.0

    intraday_position: float = 0.0

    # =====================================================
    # Market Intelligence
    # =====================================================

    trend: str = "NEUTRAL"
    momentum: str = "NORMAL"

    score: int = 0
    confidence: int = 0

    # =====================================================
    # Signal Engine
    # =====================================================

    signal: str = "WAIT"

    direction: str = "NEUTRAL"

    option_type: str = "NONE"

    strategy: str = "NONE"

    signal_strength: int = 0

    # =====================================================
    # Decision Engine
    # =====================================================

    action: str = "NO TRADE"

    setup_quality: str = "C"

    decision_reason: str = "No setup"

    # =====================================================
    # Option Recommendation
    # =====================================================

    strike: str = "-"

    expiry: str = "-"

    option_symbol: str = "-"