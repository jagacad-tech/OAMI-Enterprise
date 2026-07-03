"""
OAMI Enterprise
Scanner Engine
"""

from app.market.models import MarketSnapshot
from app.market.indicators import IndicatorEngine
from app.providers.openalgo import OpenAlgoProvider


class Scanner:
    """
    Performs market analysis for a single symbol.
    """

    def __init__(self):

        self.provider = OpenAlgoProvider()
        self.indicators = IndicatorEngine()

    def scan(self, symbol: str) -> MarketSnapshot:

        # Get market data from provider
        snapshot = self.provider.get_snapshot(symbol)

        # Analyze market data
        snapshot = self.indicators.analyze(snapshot)

        return snapshot