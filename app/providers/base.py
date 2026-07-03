"""
OAMI Enterprise
Market Data Provider Interface
"""

from abc import ABC, abstractmethod

from app.market.models import MarketSnapshot


class MarketDataInterface(ABC):
    """
    Base interface for all market data providers.
    """

    @abstractmethod
    def get_snapshot(self, symbol: str) -> MarketSnapshot:
        """
        Return the latest market snapshot.
        """
        pass