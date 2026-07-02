"""
OAMI Enterprise
Scanner Engine
"""

from app.market.models import MarketSnapshot
from app.market.market_data import MarketDataProvider


class Scanner:
    """
    Performs market analysis for a single symbol.
    """

    def __init__(self):
        self.market_data = MarketDataProvider()

    def scan(self, symbol: str) -> MarketSnapshot:
        """
        Scan a symbol and return a MarketSnapshot.
        """

        # Create empty snapshot
        snapshot = MarketSnapshot(symbol=symbol)

        # Fill snapshot with market data
        snapshot = self.market_data.get_snapshot(snapshot)

        return snapshot