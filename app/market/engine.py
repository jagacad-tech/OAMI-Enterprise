"""
OAMI Enterprise
Market Intelligence Engine
"""

from app.market.symbols import SymbolManager


class MarketEngine:
    """Main controller for the Market Intelligence Engine."""

    def __init__(self, watchlist="custom"):
        self.symbol_manager = SymbolManager(watchlist)

    def start(self):
        print("=" * 60)
        print("OAMI MARKET INTELLIGENCE ENGINE")
        print("=" * 60)

        symbols = self.symbol_manager.load()

        print(f"Watchlist Loaded : {len(symbols)} symbols")
        print()

        for symbol in symbols:
            print(f"Scanning : {symbol}")

        print()
        print("Market Engine Ready")