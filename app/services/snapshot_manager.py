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

    def update_quote(self, quote):
        """
        Update MarketSnapshot from OpenAlgo Quote
        """

        symbol = quote["symbol"]
        data = quote["data"]

        self.snapshots[symbol] = MarketSnapshot(
            symbol=symbol,
            exchange=quote.get("exchange", "NSE"),
            timestamp=data.get("timestamp"),

            open=data.get("open", 0.0),
            high=data.get("high", 0.0),
            low=data.get("low", 0.0),
            close=data.get("close", 0.0),

            ltp=data.get("ltp", 0.0),
            volume=data.get("volume", 0),
            
            # --------------------------
            # Level-5 Order Book
            # --------------------------
            depth=data.get("depth"),
        )

    def get(self, symbol):
        """
        Get snapshot by symbol
        """
        return self.snapshots.get(symbol)

    def all(self):
        """
        Return all snapshots
        """
        return self.snapshots.copy()


# --------------------------------------------------------
# Global Singleton
# --------------------------------------------------------

snapshot_manager = SnapshotManager()