"""
OAMI Enterprise
Snapshot Manager
"""

from contextlib import contextmanager
import threading

from app.market.models import MarketSnapshot


class SnapshotManager:
    """
    Stores the latest snapshot for every symbol.
    """

    def __init__(self):
        self.snapshots = {}
        self._state_lock = threading.Lock()
        self._symbol_locks = {}

    def _symbol_lock(self, symbol):
        """Return the stable lock for one snapshot without serializing symbols."""
        with self._state_lock:
            return self._symbol_locks.setdefault(symbol, threading.RLock())

    @contextmanager
    def symbol_lock(self, symbol):
        """Serialize a feed update and a scanner pass for the same symbol."""
        with self._symbol_lock(symbol):
            yield

    # --------------------------------------------------------
    # Quote Update (MODE 2)
    # --------------------------------------------------------

    def update_quote(self, quote):

        symbol = quote["symbol"]
        data = quote["data"]

        with self.symbol_lock(symbol):
            # Create snapshot only once.
            with self._state_lock:
                if symbol not in self.snapshots:
                    self.snapshots[symbol] = MarketSnapshot(
                        symbol=symbol,
                        exchange=quote.get("exchange", "NSE"),
                    )
                snapshot = self.snapshots[symbol]

            # Update quote fields only.
            snapshot.timestamp = data.get("timestamp", snapshot.timestamp)
            snapshot.quote_updated_at = data.get("timestamp", snapshot.quote_updated_at)

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

        with self.symbol_lock(symbol):
            # Create snapshot if quote hasn't arrived yet.
            with self._state_lock:
                if symbol not in self.snapshots:
                    self.snapshots[symbol] = MarketSnapshot(
                        symbol=symbol,
                        exchange=quote.get("exchange", "NSE"),
                    )
                snapshot = self.snapshots[symbol]

            snapshot.timestamp = data.get("timestamp", snapshot.timestamp)
            snapshot.depth_updated_at = data.get("timestamp", snapshot.depth_updated_at)
            snapshot.ltp = data.get("ltp", snapshot.ltp)

            # Only update depth.
            snapshot.depth = data.get("depth", snapshot.depth)

    # --------------------------------------------------------
    # Access
    # --------------------------------------------------------

    def get(self, symbol):
        with self._state_lock:
            return self.snapshots.get(symbol)

    def all(self):
        with self._state_lock:
            return self.snapshots.copy()


# --------------------------------------------------------
# Global Singleton
# --------------------------------------------------------

snapshot_manager = SnapshotManager()
