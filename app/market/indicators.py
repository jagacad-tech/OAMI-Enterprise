"""
OAMI Enterprise
Indicator Engine
"""
from app.services.volume_manager import volume_manager

class IndicatorEngine:

    def analyze(self, snapshot):

        # -----------------------------
        # Price Change
        # -----------------------------

        snapshot.change = snapshot.ltp - snapshot.close

        if snapshot.close > 0:

            snapshot.change_pct = (
                snapshot.change / snapshot.close
            ) * 100

        # -------------------------------------------------
        # Relative Volume (RVOL)
        # -------------------------------------------------

        avg_volume = volume_manager.average(snapshot.symbol)

        snapshot.rvol = round(
            snapshot.volume / avg_volume,
            2
        )

        # -----------------------------
        # Day Range
        # -----------------------------

        snapshot.day_range = snapshot.high - snapshot.low

        if snapshot.low > 0:

            snapshot.day_range_pct = (
                snapshot.day_range / snapshot.low
            ) * 100

        # -----------------------------
        # High / Low Distance
        # -----------------------------

        snapshot.distance_from_high = (
            snapshot.high - snapshot.ltp
        )

        snapshot.distance_from_low = (
            snapshot.ltp - snapshot.low
        )

        # -----------------------------
        # Intraday Position
        # -----------------------------

        if snapshot.high > snapshot.low:

            snapshot.intraday_position = (
                (snapshot.ltp - snapshot.low)
                /
                (snapshot.high - snapshot.low)
            ) * 100

        else:

            snapshot.intraday_position = 50.0

        # -----------------------------
        # Trend
        # -----------------------------

        if snapshot.ltp > snapshot.open:

            snapshot.trend = "BULLISH"

        elif snapshot.ltp < snapshot.open:

            snapshot.trend = "BEARISH"

        else:

            snapshot.trend = "NEUTRAL"

        # -----------------------------
        # Momentum
        # -----------------------------

        if abs(snapshot.change_pct) >= 2:

            snapshot.momentum = "STRONG"

        elif abs(snapshot.change_pct) >= 1:

            snapshot.momentum = "MEDIUM"

        else:

            snapshot.momentum = "LOW"

        return snapshot