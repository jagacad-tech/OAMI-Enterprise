"""
OAMI Enterprise
Indicator Engine
"""

from app.market.models import MarketSnapshot
from app.market.scoring import ScoreEngine


class IndicatorEngine:

    def __init__(self):

        self.score_engine = ScoreEngine()

    def analyze(self, snapshot: MarketSnapshot) -> MarketSnapshot:

        # Trend

        if snapshot.ltp >= snapshot.open:
            snapshot.trend = "BULLISH"

        else:
            snapshot.trend = "BEARISH"

        # Score

        snapshot = self.score_engine.calculate(snapshot)

        return snapshot