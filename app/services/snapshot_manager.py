"""
OAMI Enterprise
Snapshot Manager

Maintains the latest market snapshot for every symbol.
"""

from typing import Dict, Optional

from app.market.models import MarketSnapshot


class SnapshotManager:
    """
    Central in-memory cache for market snapshots.
    """

    def __init__(self):

        self._snapshots: Dict[str, MarketSnapshot] = {}

    def update(self, snapshot: MarketSnapshot) -> None:
        """
        Store or update a snapshot.
        """

        self._snapshots[snapshot.symbol] = snapshot

    def get(self, symbol: str) -> Optional[MarketSnapshot]:
        """
        Get latest snapshot for a symbol.
        """

        return self._snapshots.get(symbol)

    def exists(self, symbol: str) -> bool:
        """
        Check if snapshot exists.
        """

        return symbol in self._snapshots

    def all(self) -> Dict[str, MarketSnapshot]:
        """
        Return all cached snapshots.
        """

        return self._snapshots

    def clear(self) -> None:
        """
        Clear cache.
        """

        self._snapshots.clear()