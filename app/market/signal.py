"""
OAMI Enterprise
Signal Engine
"""


class SignalEngine:

    def analyze(self, snapshot):

        # ----------------------------------
        # Default
        # ----------------------------------

        snapshot.direction = "NEUTRAL"
        snapshot.option_type = "NONE"
        snapshot.strategy = "NONE"
        snapshot.signal_strength = 0

        # ----------------------------------
        # Bullish
        # ----------------------------------

        if snapshot.trend == "BULLISH":

            snapshot.direction = "BULLISH"
            snapshot.option_type = "CE"

            if snapshot.momentum == "STRONG":

                snapshot.strategy = "MOMENTUM"
                snapshot.signal_strength = 90

            elif snapshot.momentum == "MEDIUM":

                snapshot.strategy = "SETUP"
                snapshot.signal_strength = 70

            else:

                snapshot.strategy = "SETUP"
                snapshot.signal_strength = 50

        # ----------------------------------
        # Bearish
        # ----------------------------------

        elif snapshot.trend == "BEARISH":

            snapshot.direction = "BEARISH"
            snapshot.option_type = "PE"

            if snapshot.momentum == "STRONG":

                snapshot.strategy = "MOMENTUM"
                snapshot.signal_strength = 90

            elif snapshot.momentum == "MEDIUM":

                snapshot.strategy = "SETUP"
                snapshot.signal_strength = 70

            else:

                snapshot.strategy = "SETUP"
                snapshot.signal_strength = 50

        return snapshot