"""
OAMI Enterprise
OpenAlgo Provider
"""

from app.market.models import MarketSnapshot
from app.providers.base import MarketDataInterface


class OpenAlgoProvider(MarketDataInterface):
    """
    OpenAlgo Market Data Provider.

    Placeholder implementation.
    """

    def get_snapshot(self, symbol: str) -> MarketSnapshot:

        snapshot = MarketSnapshot(symbol=symbol)

        # Dummy values
        snapshot.status = "READY"
        snapshot.ltp = 100.00
        snapshot.open = 99.50
        snapshot.high = 101.20
        snapshot.low = 99.10
        snapshot.close = 100.50
        snapshot.volume = 100000

        return snapshot