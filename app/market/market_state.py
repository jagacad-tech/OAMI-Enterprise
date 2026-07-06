"""
OAMI Enterprise
Market State Engine
"""


class MarketStateEngine:

    def analyze(self, snapshots):

        total = len(snapshots)

        if total == 0:

            return {
                "state": "UNKNOWN",
                "bullish": 0,
                "bearish": 0,
                "neutral": 0,
                "avg_score": 0,
                "avg_rvol": 0,
            }

        bullish = sum(
            1 for s in snapshots
            if s.trend == "BULLISH"
        )

        bearish = sum(
            1 for s in snapshots
            if s.trend == "BEARISH"
        )

        neutral = total - bullish - bearish

        avg_score = sum(
            s.score for s in snapshots
        ) / total

        avg_rvol = sum(
            s.rvol for s in snapshots
        ) / total

        # ------------------------
        # State
        # ------------------------

        if bullish >= total * 0.70:

            state = "TRENDING_BULL"

        elif bearish >= total * 0.70:

            state = "TRENDING_BEAR"

        elif avg_rvol >= 2:

            state = "HIGH_ACTIVITY"

        else:

            state = "SIDEWAYS"

        return {

            "state": state,

            "bullish": bullish,

            "bearish": bearish,

            "neutral": neutral,

            "avg_score": round(avg_score, 1),

            "avg_rvol": round(avg_rvol, 2),
        }