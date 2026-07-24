"""
OAMI Enterprise
Trade Plan Engine
"""


class TradePlanEngine:

    def analyze(self, snapshot):

        snapshot.entry_price = 0.0
        snapshot.stop_loss = 0.0
        snapshot.target1 = 0.0
        snapshot.target2 = 0.0
        snapshot.risk_reward = 0.0

        if snapshot.lifecycle_state not in {"NEW BUY", "CONFIRMED"}:
            return snapshot

        # ------------------------------------------------
        # BUY CE
        # ------------------------------------------------

        if snapshot.option_type == "CE":

            snapshot.entry_price = round(snapshot.ltp + 0.20, 2)

            snapshot.stop_loss = round(snapshot.low, 2)

            risk = snapshot.entry_price - snapshot.stop_loss

            snapshot.target1 = round(
                snapshot.entry_price + risk,
                2
            )

            snapshot.target2 = round(
                snapshot.entry_price + (risk * 2),
                2
            )

        # ------------------------------------------------
        # BUY PE
        # ------------------------------------------------

        elif snapshot.option_type == "PE":

            snapshot.entry_price = round(snapshot.ltp - 0.20, 2)

            snapshot.stop_loss = round(snapshot.high, 2)

            risk = snapshot.stop_loss - snapshot.entry_price

            snapshot.target1 = round(
                snapshot.entry_price - risk,
                2
            )

            snapshot.target2 = round(
                snapshot.entry_price - (risk * 2),
                2
            )

        if risk > 0:

            reward = abs(
                snapshot.target2 - snapshot.entry_price
            )

            snapshot.risk_reward = round(
                reward / risk,
                2
            )

        return snapshot
