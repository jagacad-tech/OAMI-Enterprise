"""
OAMI Enterprise
Market Intelligence Engine
"""

from app.market.symbols import SymbolManager
from app.market.scanner import Scanner


class MarketEngine:
    """
    Main controller for OAMI Market Intelligence.
    """

    def __init__(self, watchlist="custom"):

        self.symbol_manager = SymbolManager(watchlist)
        self.scanner = Scanner()

    def start(self):

        print("=" * 70)
        print("OAMI MARKET INTELLIGENCE ENGINE")
        print("=" * 70)

        symbols = self.symbol_manager.load()

        print(f"Loaded {len(symbols)} symbols\n")

        results = []

        for symbol in symbols:

            result = self.scanner.scan(symbol)

            results.append(result)

            print(result)

        print("\nScanner Completed")

        return results