"""
OAMI Enterprise
Scanner Engine
"""

from app.market.models import MarketSnapshot
from app.market.market_data import MarketDataProvider
from app.market.indicators import IndicatorEngine


class Scanner:

    def __init__(self):

        self.market_data = MarketDataProvider()
        self.indicators = IndicatorEngine()

    def scan(self, symbol: str) -> MarketSnapshot:

        snapshot = MarketSnapshot(symbol=symbol)

        # Load market data
        snapshot = self.market_data.get_snapshot(snapshot)

        # Analyze indicators
        snapshot = self.indicators.analyze(snapshot)

        return snapshot