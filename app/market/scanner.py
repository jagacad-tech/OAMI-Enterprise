from app.market.indicators import IndicatorEngine
from app.market.scoring import ScoringEngine
from app.market.signal import SignalEngine
from app.market.decision import DecisionEngine
from app.market.option_selector import OptionSelector
from app.market.ranking import RankingEngine
from app.services.snapshot_manager import snapshot_manager
from app.market.trade_plan import TradePlanEngine
from app.services.signal_memory import signal_memory

class Scanner:

    def __init__(self):

        self.indicators = IndicatorEngine()
        self.scoring = ScoringEngine()
        self.signal = SignalEngine()
        self.decision = DecisionEngine()
        self.option_selector = OptionSelector()
        self.ranking = RankingEngine()
        self.trade_plan = TradePlanEngine()

    def scan(self):

        snapshots = snapshot_manager.all()

        results = []

        for symbol, snapshot in snapshots.items():

            snapshot = self.indicators.analyze(snapshot)
            snapshot = self.scoring.score(snapshot)
            snapshot = self.signal.analyze(snapshot)
            snapshot = self.decision.analyze(snapshot)
            record = signal_memory.update(
                snapshot.symbol,
                snapshot.action
            )

            snapshot.signal_state = record.state
            snapshot.signal_age = record.age_seconds
            snapshot = self.option_selector.analyze(snapshot)
            snapshot = self.trade_plan.analyze(snapshot)

            results.append(snapshot)

        return self.ranking.sort(results)