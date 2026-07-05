"""
OAMI Enterprise
Scoring Engine
"""


class ScoringEngine:

    def calculate(self, snapshot):

        score = 0

        if snapshot.trend == "BULLISH":
            score += 50

        if snapshot.volume and snapshot.volume > 1_000_000:
            score += 50

        return score