"""
OAMI Enterprise
Signal Engine
"""


class SignalEngine:

    def analyze(self, snapshot):

        snapshot.signal = "WAIT"
        snapshot.signal_strength = 0

        # -------------------------
        # BUY
        # -------------------------

        if (
            snapshot.trend == "BULLISH"
            and snapshot.rvol >= 2
            and snapshot.intraday_position >= 70
            and snapshot.score >= 60
        ):

            snapshot.signal = "BUY"
            snapshot.signal_strength = 90

        # -------------------------
        # SELL
        # -------------------------

        elif (
            snapshot.trend == "BEARISH"
            and snapshot.rvol >= 2
            and snapshot.intraday_position <= 30
            and snapshot.score >= 30
        ):

            snapshot.signal = "SELL"
            snapshot.signal_strength = 90

        # -------------------------
        # WATCH
        # -------------------------

        elif snapshot.score >= 20:

            snapshot.signal = "WATCH"
            snapshot.signal_strength = 50

        return snapshot