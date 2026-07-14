"""
OAMI Enterprise
Depth Engine

Computes:
- Bid Pressure
- Ask Pressure
- Order Book Imbalance (OBI)
- Spread
- Support Wall
- Resistance Wall
"""

class DepthEngine:

    def analyze(self, snapshot):

        # ----------------------------------------
        # No Snapshot
        # ----------------------------------------

        if snapshot is None:
            return None

        # ----------------------------------------
        # No Depth Received Yet
        # ----------------------------------------

        if snapshot.depth is None:

            snapshot.bid_pressure = 0
            snapshot.ask_pressure = 0
            snapshot.orderbook_imbalance = 0.0
            snapshot.spread = 0.0
            snapshot.support_wall = 0
            snapshot.resistance_wall = 0
            snapshot.orderflow = "NO_DEPTH"

            return snapshot

        # ----------------------------------------
        # Read Level-5 Book
        # ----------------------------------------

        buy = snapshot.depth.get("buy", [])
        sell = snapshot.depth.get("sell", [])
        
        print("\n================ DEPTH =================")

        print("BUY:")
        for level in buy:
            print(level)

        print("\nSELL:")
        for level in sell:
            print(level)

        print("========================================\n")
        

        print(
            f"{snapshot.symbol:<12} "
            f"BUY_LEVELS={len(buy)} "
            f"SELL_LEVELS={len(sell)}"
        )

        # ----------------------------------------
        # Bid / Ask Pressure
        # ----------------------------------------

        snapshot.bid_pressure = sum(
            level.get("quantity", 0)
            for level in buy
        )

        snapshot.ask_pressure = sum(
            level.get("quantity", 0)
            for level in sell
        )

        # ----------------------------------------
        # Order Book Imbalance
        # ----------------------------------------

        total = snapshot.bid_pressure + snapshot.ask_pressure

        if total > 0:

            snapshot.orderbook_imbalance = (
                snapshot.bid_pressure
                - snapshot.ask_pressure
            ) / total

        else:

            snapshot.orderbook_imbalance = 0.0

        # ----------------------------------------
        # Spread
        # ----------------------------------------

        if buy and sell:

            best_bid = buy[0].get("price", 0)
            best_ask = sell[0].get("price", 0)

            snapshot.spread = best_ask - best_bid

        else:

            snapshot.spread = 0.0

        # ----------------------------------------
        # Largest Bid / Ask Walls
        # ----------------------------------------

        snapshot.support_wall = max(
            (level.get("quantity", 0) for level in buy),
            default=0,
        )

        snapshot.resistance_wall = max(
            (level.get("quantity", 0) for level in sell),
            default=0,
        )

        # ----------------------------------------
        # Order Flow Classification
        # ----------------------------------------

        obi = snapshot.orderbook_imbalance

        if obi >= 0.30:
            snapshot.orderflow = "STRONG BUY"

        elif obi >= 0.10:
            snapshot.orderflow = "BUY"

        elif obi <= -0.30:
            snapshot.orderflow = "STRONG SELL"

        elif obi <= -0.10:
            snapshot.orderflow = "SELL"

        else:
            snapshot.orderflow = "NEUTRAL"

        # ----------------------------------------
        # Debug
        # ----------------------------------------

        print(
            f"{snapshot.symbol:<12} "
            f"Bid={snapshot.bid_pressure} "
            f"Ask={snapshot.ask_pressure} "
            f"OBI={snapshot.orderbook_imbalance:.2f} "
            f"Spread={snapshot.spread:.2f}"
        )

        return snapshot