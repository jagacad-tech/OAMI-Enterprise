"""
OAMI Enterprise
Decision Engine
"""


class DecisionEngine:

    def analyze(self, snapshot):

        snapshot.action = "NO TRADE"
        snapshot.setup_quality = "C"
        snapshot.decision_reason = "No valid setup"

        # ------------------------------------------------
        # BUY CE
        # ------------------------------------------------

        if (
            snapshot.signal == "BUY"
            and snapshot.option_type == "CE"
        ):

            snapshot.action = "BUY CE"

            if snapshot.score >= 90:
                snapshot.setup_quality = "A+"

            elif snapshot.score >= 75:
                snapshot.setup_quality = "A"

            elif snapshot.score >= 60:
                snapshot.setup_quality = "B"

            snapshot.decision_reason = (
                "Bullish Momentum"
            )

        # ------------------------------------------------
        # BUY PE
        # ------------------------------------------------

        elif (
            snapshot.signal == "BUY"
            and snapshot.option_type == "PE"
        ):

            snapshot.action = "BUY PE"

            if snapshot.score >= 90:
                snapshot.setup_quality = "A+"

            elif snapshot.score >= 75:
                snapshot.setup_quality = "A"

            elif snapshot.score >= 60:
                snapshot.setup_quality = "B"

            snapshot.decision_reason = (
                "Bearish Momentum"
            )

        # ------------------------------------------------
        # WATCH
        # ------------------------------------------------

        elif snapshot.signal == "WATCH":

            if snapshot.option_type == "CE":

                snapshot.action = "WATCH CE"

            elif snapshot.option_type == "PE":

                snapshot.action = "WATCH PE"

            snapshot.setup_quality = "C"

            snapshot.decision_reason = (
                "Setup Developing"
            )

        return snapshot