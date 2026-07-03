"""
OAMI Enterprise
Score Engine
"""

from app.market.models import MarketSnapshot


class ScoreEngine:
    """
    Calculates the opportunity score.
    """

    def calculate(self, snapshot: MarketSnapshot) -> MarketSnapshot:

        score = 0

        # Trend Score
        if snapshot.trend == "BULLISH":
            score += 30

        # Price Above Open
        if snapshot.ltp > snapshot.open:
            score += 20

        # Strong Close
        if snapshot.close >= snapshot.high * 0.99:
            score += 10

        snapshot.score = score

        return snapshot