"""
OAMI Enterprise
Market Intelligence Engine
"""

from app.market.symbols import SymbolManager
from app.market.scanner import Scanner
from app.market.ranking import RankingEngine


class MarketEngine:

    def __init__(self, watchlist="custom"):

        self.symbol_manager = SymbolManager(watchlist)

        self.scanner = Scanner()

        self.ranking = RankingEngine()

    def start(self):

        print("=" * 70)
        print("OAMI MARKET INTELLIGENCE ENGINE")
        print("=" * 70)

        symbols = self.symbol_manager.load()

        print(f"Loaded {len(symbols)} symbols\n")

        snapshots = []

        for symbol in symbols:

            snapshot = self.scanner.scan(symbol)

            snapshots.append(snapshot)

        snapshots = self.ranking.rank(snapshots)

        print("Ranking Results")
        print("-" * 70)

        for index, snapshot in enumerate(snapshots, start=1):

            print(
                f"{index:02d}. "
                f"{snapshot.symbol:<12} "
                f"Score={snapshot.score:<3} "
                f"Trend={snapshot.trend}"
            )

        print("\nScanner Completed")

        return snapshots