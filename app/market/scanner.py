"""
OAMI Enterprise
Market Scanner
"""

from app.market.indicators import IndicatorEngine
from app.market.scoring import ScoringEngine
from app.market.signal import SignalEngine
from app.market.decision import DecisionEngine
from app.market.option_selector import OptionSelector
from app.market.ranking import RankingEngine
from app.market.trade_plan import TradePlanEngine
from app.market.trade_lifecycle import TradeLifecycleEngine
from app.market.instrument_master import get
from app.market.indexes import INDEX_SYMBOLS
from app.services.snapshot_manager import snapshot_manager
from app.market.market_intelligence import MarketIntelligence
from app.market.depth_engine import DepthEngine
from app.observability.factory import build_lifecycle_event_bus
from app.core.logger import logger


class Scanner:

    def __init__(self):

        self.indicators = IndicatorEngine()
        self.scoring = ScoringEngine()
        self.signal = SignalEngine()
        self.decision = DecisionEngine()
        self.lifecycle_events = build_lifecycle_event_bus()
        self.lifecycle = TradeLifecycleEngine(self.decision, self.lifecycle_events)
        self.trade_plan = TradePlanEngine()
        self.option_selector = OptionSelector()
        self.ranking = RankingEngine()
        self.market_intelligence = MarketIntelligence()
        self.depth_engine = DepthEngine()
        self._scan_id = 0
        

    # -------------------------------------------------

    
    def scan(self):
        try:
            self._scan_id += 1
            snapshots = snapshot_manager.all()
            results = []

            for symbol, snapshot in snapshots.items():
                # Index ticks are presentation-only and must never reach the
                # scanner, even if one is accidentally placed in this cache.
                if symbol in INDEX_SYMBOLS:
                    continue
                processed_snapshot = self._scan_symbol(symbol, snapshot)
                if processed_snapshot is not None:
                    results.append(processed_snapshot)

            print(f"Total Results = {len(results)}")
            return self.ranking.sort(results)
        except Exception:
            # This is the last line of defence for a scanner pass.  Individual
            # symbols are isolated below, but infrastructure failures such as
            # snapshot retrieval or ranking must not terminate the scan loop.
            logger.exception("Scanner pass failed: scan_id=%s", self._scan_id)
            return []

    def _scan_symbol(self, symbol, snapshot):
        """Process one symbol without allowing it to abort the scanner pass."""
        try:
            with snapshot_manager.symbol_lock(symbol):
                return self._scan_symbol_locked(symbol, snapshot)
        except Exception:
            logger.exception(
                "Scanner symbol failed: scan_id=%s symbol=%s",
                self._scan_id,
                symbol,
            )
            return None

    def _scan_symbol_locked(self, symbol, snapshot):
        """Run the established analysis pipeline while the symbol is stable."""
        try:
            # ------------------------------------
            # Instrument Details
            # ------------------------------------

            instrument = get(snapshot.symbol)

            snapshot.instrument_type = instrument["instrument_type"]
            snapshot.strike_interval = instrument["strike_interval"]
            snapshot.lot_size = instrument["lot_size"]

            # ------------------------------------
            # Order Flow
            # ------------------------------------

            snapshot = self.depth_engine.analyze(snapshot)

            print(
                f"{snapshot.symbol:<12}"
                f" BidPressure={snapshot.bid_pressure}"
            )

            # ------------------------------------
            # Market Analysis
            # ------------------------------------

            snapshot = self.indicators.analyze(snapshot)

            snapshot = self.scoring.score(snapshot)

            snapshot = self.signal.analyze(snapshot)

            snapshot = self.decision.analyze(snapshot)

            # ------------------------------------
            # Trade Lifecycle
            # ------------------------------------

            snapshot = self.lifecycle.analyze(snapshot, scan_id=self._scan_id)

            # ------------------------------------
            # Trade Plan
            # ------------------------------------

            snapshot = self.trade_plan.analyze(snapshot)

            # ------------------------------------
            # Option Selection
            # ------------------------------------

            snapshot = self.option_selector.analyze(snapshot)

            # ------------------------------------
            # Debug
            # ------------------------------------

            if snapshot is None:
                print(f"ERROR : {symbol} snapshot became None")
                return None

            print(f"Scanner OK : {snapshot.symbol}")
            return snapshot
        except Exception:
            logger.exception(
                "Scanner symbol failed: scan_id=%s symbol=%s",
                self._scan_id,
                symbol,
            )
            return None

