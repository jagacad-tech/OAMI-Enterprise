"""
OAMI Enterprise
Options Signal Engine
"""


class SignalEngine:

    def analyze(self, snapshot):

        snapshot.signal = "WAIT"
        snapshot.direction = "NEUTRAL"
        snapshot.option_type = "NONE"
        snapshot.strategy = "NONE"
        snapshot.signal_strength = 0

        # -------------------------
        # Bullish Opportunity
        # -------------------------

        if (
            snapshot.trend == "BULLISH"
            and snapshot.rvol >= 2
            and snapshot.intraday_position >= 70
            and snapshot.score >= 30
        ):

            snapshot.signal = "BUY"
            snapshot.direction = "BULLISH"
            snapshot.option_type = "CE"
            snapshot.strategy = "MOMENTUM"
            snapshot.signal_strength = 90

        # -------------------------
        # Bearish Opportunity
        # -------------------------

        elif (
            snapshot.trend == "BEARISH"
            and snapshot.rvol >= 2
            and snapshot.intraday_position <= 30
            and snapshot.score >= 30
        ):

            snapshot.signal = "BUY"
            snapshot.direction = "BEARISH"
            snapshot.option_type = "PE"
            snapshot.strategy = "MOMENTUM"
            snapshot.signal_strength = 90

        # -------------------------
        # Watch
        # -------------------------

        elif snapshot.score >= 20:

            snapshot.signal = "WATCH"

            snapshot.direction = snapshot.trend

            if snapshot.trend == "BULLISH":
                snapshot.option_type = "CE"

            elif snapshot.trend == "BEARISH":
                snapshot.option_type = "PE"

            snapshot.strategy = "SETUP"

            snapshot.signal_strength = 50

        return snapshot