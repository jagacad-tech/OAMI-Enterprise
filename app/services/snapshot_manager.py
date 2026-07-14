"""
OAMI Enterprise
Snapshot Manager
"""

from app.market.models import MarketSnapshot


class SnapshotManager:
    """
    Stores the latest snapshot for every symbol.
    """

    def __init__(self):
        self.snapshots = {}

    # --------------------------------------------------------
    # Quote Update (MODE 2)
    # --------------------------------------------------------

    def update_quote(self, quote):

        symbol = quote["symbol"]
        data = quote["data"]

        # Create snapshot only once
        if symbol not in self.snapshots:

            self.snapshots[symbol] = MarketSnapshot(
                symbol=symbol,
                exchange=quote.get("exchange", "NSE"),
            )

        snapshot = self.snapshots[symbol]

        # Update quote fields only
        snapshot.timestamp = data.get("timestamp", snapshot.timestamp)

        snapshot.open = data.get("open", snapshot.open)
        snapshot.high = data.get("high", snapshot.high)
        snapshot.low = data.get("low", snapshot.low)
        snapshot.close = data.get("close", snapshot.close)

        snapshot.ltp = data.get("ltp", snapshot.ltp)
        snapshot.volume = data.get("volume", snapshot.volume)

    # --------------------------------------------------------
    # Depth Update (MODE 3)
    # --------------------------------------------------------

    def update_depth(self, quote):

        symbol = quote["symbol"]
        data = quote["data"]

        # Create snapshot if quote hasn't arrived yet
        if symbol not in self.snapshots:

            self.snapshots[symbol] = MarketSnapshot(
                symbol=symbol,
                exchange=quote.get("exchange", "NSE"),
            )

        snapshot = self.snapshots[symbol]

        snapshot.timestamp = data.get("timestamp", snapshot.timestamp)
        snapshot.ltp = data.get("ltp", snapshot.ltp)

        # Only update depth
        snapshot.depth = data.get("depth", snapshot.depth)

    # --------------------------------------------------------
    # Access
    # --------------------------------------------------------

    def get(self, symbol):
        return self.snapshots.get(symbol)

    def all(self):
        return self.snapshots.copy()


# --------------------------------------------------------
# Global Singleton
# --------------------------------------------------------

snapshot_manager = SnapshotManager()