"""
OAMI Enterprise
Indicator Engine
"""


class IndicatorEngine:

    def analyze(self, snapshot):

        if snapshot.ltp and snapshot.open:

            if snapshot.ltp > snapshot.open:
                snapshot.trend = "BULLISH"

            elif snapshot.ltp < snapshot.open:
                snapshot.trend = "BEARISH"

            else:
                snapshot.trend = "NEUTRAL"

        return snapshot