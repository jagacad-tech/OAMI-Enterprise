"""
OAMI Enterprise
Market Intelligence Engine
"""

from app.market.symbols import SymbolManager
from app.market.scanner import Scanner
from app.market.ranking import RankingEngine
from app.core.logger import logger


class MarketEngine:

    def __init__(self, watchlist="custom"):

        self.symbol_manager = SymbolManager(watchlist)

        self.scanner = Scanner()

        self.ranking = RankingEngine()

    def start(self):
        try:
            print("=" * 70)
            print("OAMI MARKET INTELLIGENCE ENGINE")
            print("=" * 70)

            symbols = self.symbol_manager.load()
            print(f"Loaded {len(symbols)} symbols\n")

            # Scanner.scan() is a full-snapshot pass.  Calling it once avoids
            # re-scanning the whole snapshot set for every configured symbol.
            snapshots = self.scanner.scan()

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
        except Exception:
            logger.exception("Market engine scanner pass failed")
            return []
