"""
OAMI Enterprise
Market Data Provider
"""

from app.market.models import MarketSnapshot


class MarketDataProvider:
    """
    Supplies market data.

    Currently returns dummy data.
    Later this class will connect to OpenAlgo.
    """

    def get_snapshot(self, snapshot: MarketSnapshot) -> MarketSnapshot:

        snapshot.ltp = 100.00
        snapshot.open = 99.50
        snapshot.high = 101.20
        snapshot.low = 99.10
        snapshot.close = 100.50
        snapshot.volume = 100000

        return snapshot