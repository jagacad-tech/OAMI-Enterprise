"""
OAMI Enterprise
Scoring Engine
"""


class ScoringEngine:

    def calculate(self, snapshot):

        score = 0

        # Trend
        if snapshot.trend == "BULLISH":
            score += 30

        # Momentum
        if snapshot.momentum == "STRONG":
            score += 30

        elif snapshot.momentum == "MEDIUM":
            score += 20

        else:
            score += 10

        # Volume
        if snapshot.volume > 10_000_000:
            score += 40

        elif snapshot.volume > 5_000_000:
            score += 25

        else:
            score += 10

        snapshot.confidence = score

        return score