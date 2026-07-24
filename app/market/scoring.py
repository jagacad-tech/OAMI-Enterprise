"""
OAMI Enterprise
Scoring Engine V3

Scores price action, participation, and Level-5 order-flow confirmation.
"""


class ScoringEngine:

    def score(self, snapshot):

        total = (
            self.trend_score(snapshot)
            + self.momentum_score(snapshot)
            + self.position_score(snapshot)
            + self.volume_score(snapshot)
            + self.order_flow_score(snapshot)
            + self.liquidity_score(snapshot)
        )

        snapshot.score = total
        snapshot.confidence = min(100, total)

        return snapshot

    # -------------------------------------------------

    def trend_score(self, snapshot):

        if snapshot.trend in {"BULLISH", "BEARISH"}:
            return 25

        return 0

    # -------------------------------------------------

    def momentum_score(self, snapshot):

        if snapshot.momentum == "STRONG":
            return 20

        if snapshot.momentum == "MEDIUM":
            return 10

        return 5

    # -------------------------------------------------

    def position_score(self, snapshot):

        position = snapshot.intraday_position

        if snapshot.trend == "BULLISH":
            if position >= 90:
                return 15
            if position >= 75:
                return 10
            if position >= 60:
                return 5

        elif snapshot.trend == "BEARISH":
            if position <= 10:
                return 15
            if position <= 25:
                return 10
            if position <= 40:
                return 5

        return 0

    # -------------------------------------------------

    def volume_score(self, snapshot):

        if snapshot.rvol >= 2.0:
            return 15

        if snapshot.rvol >= 1.3:
            return 10

        if snapshot.rvol > 0:
            return 5

        return 0

    # -------------------------------------------------

    def order_flow_score(self, snapshot):
        """Score depth only when it confirms the current price direction."""

        obi = snapshot.orderbook_imbalance

        if snapshot.trend == "BULLISH":
            if snapshot.bid_pressure <= snapshot.ask_pressure or obi <= 0:
                return 0
            if obi >= 0.30:
                return 20
            if obi >= 0.10:
                return 12

        elif snapshot.trend == "BEARISH":
            if snapshot.ask_pressure <= snapshot.bid_pressure or obi >= 0:
                return 0
            if obi <= -0.30:
                return 20
            if obi <= -0.10:
                return 12

        return 0

    # -------------------------------------------------

    def liquidity_score(self, snapshot):
        """Reward a valid, instrument-appropriate tight spread."""

        if snapshot.spread <= 0:
            return 0

        if snapshot.spread <= self.spread_limit(snapshot):
            return 5

        return 0

    # -------------------------------------------------

    def spread_limit(self, snapshot):
        """Isolated default limits, ready for instrument-specific tuning."""

        limits = {
            "INDEX": 0.0005,
            "STOCK": 0.0010,
        }

        percentage_limit = limits.get(snapshot.instrument_type, 0.0010)
        reference_price = max(snapshot.ltp, 1.0)

        return reference_price * percentage_limit
