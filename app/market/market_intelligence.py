"""
OAMI Enterprise
Market Intelligence Engine
"""


class MarketIntelligence:

    def analyze(self, snapshots):

        market = {

            "bias": "NEUTRAL",

            "bullish": 0,

            "bearish": 0,

            "neutral": 0,

            "strength": 0,

        }

        for snapshot in snapshots:

            if snapshot.trend == "BULLISH":

                market["bullish"] += 1

            elif snapshot.trend == "BEARISH":

                market["bearish"] += 1

            else:

                market["neutral"] += 1

        total = max(len(snapshots), 1)

        if market["bullish"] > market["bearish"]:

            market["bias"] = "BULLISH"

        elif market["bearish"] > market["bullish"]:

            market["bias"] = "BEARISH"

        else:

            market["bias"] = "SIDEWAYS"

        market["strength"] = int(

            max(

                market["bullish"],

                market["bearish"]

            )

            / total

            * 100

        )

        return market