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
from app.market.instrument_master import get
from app.services.snapshot_manager import snapshot_manager
from app.services.signal_memory import signal_memory
from app.market.market_intelligence import MarketIntelligence


class Scanner:

    def __init__(self):

        self.indicators = IndicatorEngine()
        self.scoring = ScoringEngine()
        self.signal = SignalEngine()
        self.decision = DecisionEngine()
        self.option_selector = OptionSelector()
        self.trade_plan = TradePlanEngine()
        self.ranking = RankingEngine()
        self.market_intelligence = MarketIntelligence()

    # -------------------------------------------------

    def scan(self):

        snapshots = snapshot_manager.all()

        results = []

        for symbol, snapshot in snapshots.items():

            # ------------------------------------
            # Instrument Details
            # ------------------------------------

            instrument = get(snapshot.symbol)

            snapshot.instrument_type = instrument["instrument_type"]
            snapshot.strike_interval = instrument["strike_interval"]
            snapshot.lot_size = instrument["lot_size"]

            # ------------------------------------
            # Market Analysis
            # ------------------------------------

            snapshot = self.indicators.analyze(snapshot)

            snapshot = self.scoring.score(snapshot)

            snapshot = self.signal.analyze(snapshot)

            snapshot = self.decision.analyze(snapshot)

            # ------------------------------------
            # Signal Memory
            # ------------------------------------

            record = signal_memory.update(

                symbol=snapshot.symbol,

                signal=snapshot.action,

                confidence=snapshot.confidence,

                score=snapshot.score,

                rvol=snapshot.rvol

            )

            snapshot.signal_state = record.state
            snapshot.signal_age = record.age_seconds
            

            # ------------------------------------
            # Option Selection
            # ------------------------------------

            snapshot = self.option_selector.analyze(snapshot)

            # ------------------------------------
            # Trade Plan
            # ------------------------------------

            snapshot = self.trade_plan.analyze(snapshot)

            results.append(snapshot)

        return self.ranking.sort(results)