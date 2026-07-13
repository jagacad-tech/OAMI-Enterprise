"""
OAMI Enterprise
Depth Engine
"""


class DepthEngine:

    def analyze(self, snapshot):

        # ----------------------------------------
        # TEST 1 - Is Depth Available?
        # ----------------------------------------

        if snapshot.depth is None:

            print(f"{snapshot.symbol:<12} -> NO DEPTH")

            return snapshot

        print(f"{snapshot.symbol:<12} -> DEPTH RECEIVED")

        buy = snapshot.depth.get("buy", [])
        sell = snapshot.depth.get("sell", [])

        print(
            f"{snapshot.symbol:<12} "
            f"BUY_LEVELS={len(buy)} "
            f"SELL_LEVELS={len(sell)}"
        )

        # ------------------------------------
        # Total Bid / Ask Quantity
        # ------------------------------------

        snapshot.bid_pressure = sum(
            level["quantity"]
            for level in buy
        )

        snapshot.ask_pressure = sum(
            level["quantity"]
            for level in sell
        )

        # ------------------------------------
        # Order Book Imbalance
        # ------------------------------------

        total = snapshot.bid_pressure + snapshot.ask_pressure

        if total > 0:

            snapshot.orderbook_