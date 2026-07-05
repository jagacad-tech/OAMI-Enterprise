"""
OAMI Enterprise
Scoring Engine V2
"""


class ScoringEngine:

    def score(self, snapshot):

        trend_score = self.trend_score(snapshot)

        momentum_score = self.momentum_score(snapshot)

        position_score = self.position_score(snapshot)

        volume_score = self.volume_score(snapshot)

        total = (
            trend_score
            + momentum_score
            + position_score
            + volume_score
        )

        snapshot.score = total

        snapshot.confidence = min(100, total)

        return snapshot

    # -------------------------------------------------

    def trend_score(self, snapshot):

        if snapshot.trend == "BULLISH":
            return 30

        if snapshot.trend == "NEUTRAL":
            return 15

        return 0

    # -------------------------------------------------

    def momentum_score(self, snapshot):

        if snapshot.momentum == "HIGH":
            return 20

        if snapshot.momentum == "MEDIUM":
            return 10

        return 5

    # -------------------------------------------------

    def position_score(self, snapshot):

        pos = snapshot.intraday_position

        if pos >= 90:
            return 30

        if pos >= 75:
            return 20

        if pos >= 60:
            return 10

        if pos >= 40:
            return 5

        return 0

    # -------------------------------------------------

    def volume_score(self, snapshot):

        vol = snapshot.volume

        if vol >= 20_000_000:
            return 20

        if vol >= 10_000_000:
            return 15

        if vol >= 5_000_000:
            return 10

        return 5