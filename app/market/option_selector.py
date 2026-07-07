"""
OAMI Enterprise
Option Selection Engine
"""


class OptionSelector:

    def analyze(self, snapshot):

        print(
            f"{snapshot.symbol:<12}"
            f"ACTION={snapshot.action:<10}"
            f"OPTION={snapshot.option_type:<5}"
        )

        snapshot.strike = "-"
        snapshot.expiry = "-"
        snapshot.option_symbol = "-"

        # ---------------------------------
        # No Trade
        # ---------------------------------

        if snapshot.action == "NO TRADE":

            print(f" -> STRIKE={snapshot.strike}")

            return snapshot

        # ---------------------------------
        # ATM Strike
        # ---------------------------------

        strike = self.round_to_strike(snapshot.ltp)

        if snapshot.option_type == "CE":

            snapshot.strike = f"{strike} CE"

        elif snapshot.option_type == "PE":

            snapshot.strike = f"{strike} PE"

        snapshot.option_symbol = snapshot.strike
        snapshot.expiry = "NEXT WEEK"

        print(f" -> STRIKE={snapshot.strike}")

        return snapshot

    # -------------------------------------

    def round_to_strike(self, price):

        return round(price / 10) * 10