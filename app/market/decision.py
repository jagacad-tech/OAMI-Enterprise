"""
OAMI Enterprise
Decision Engine
"""


class DecisionEngine:

    def analyze(self, snapshot):

        snapshot.signal = "WAIT"
        snapshot.action = "NO TRADE"
        snapshot.setup_quality = "C"
        snapshot.decision_reason = "No valid setup"

        # =====================================
        # BUY
        # =====================================

        if (
            snapshot.score >= 70
            and snapshot.rvol >= 2
        ):

            snapshot.signal = "BUY"

            if snapshot.option_type == "CE":

                snapshot.action = "BUY CE"

                snapshot.decision_reason = (
                    "Bullish trend with strong participation"
                )

            elif snapshot.option_type == "PE":

                snapshot.action = "BUY PE"

                snapshot.decision_reason = (
                    "Bearish trend with strong participation"
                )

        # =====================================
        # WATCH
        # =====================================

        elif snapshot.score >= 30:

            snapshot.signal = "WATCH"

            if snapshot.option_type == "CE":

                snapshot.action = "WATCH CE"

            elif snapshot.option_type == "PE":

                snapshot.action = "WATCH PE"

            snapshot.decision_reason = (
                "Setup developing"
            )

        # =====================================
        # Quality
        # =====================================

        if snapshot.score >= 90:

            snapshot.setup_quality = "A+"

        elif snapshot.score >= 75:

            snapshot.setup_quality = "A"

        elif snapshot.score >= 60:

            snapshot.setup_quality = "B"

        else:

            snapshot.setup_quality = "C"

        # =====================================
        # Live Debug (Temporary)
        # =====================================

        if snapshot.action != "NO TRADE":

            print(
                f"[{snapshot.action}] "
                f"{snapshot.symbol:<12} "
                f"Score={snapshot.score:<3} "
                f"RVOL={snapshot.rvol:.2f} "
                f"Trend={snapshot.trend:<8} "
                f"Momentum={snapshot.momentum:<8} "
                f"Pos={snapshot.intraday_position:.1f} "
                f"Reason={snapshot.decision_reason}"
            )

        return snapshot