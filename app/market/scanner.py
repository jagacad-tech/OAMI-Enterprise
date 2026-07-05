"""
OAMI Enterprise
Live Market Scanner
"""

from app.services.snapshot_manager import snapshot_manager
from app.market.indicators import IndicatorEngine
from app.market.scoring import ScoringEngine
from app.market.ranking import RankingEngine
from app.services.volume_manager import volume_manager


class Scanner:

    def __init__(self):

        self.indicators = IndicatorEngine()
        self.scoring = ScoringEngine()
        self.ranking = RankingEngine()

    def scan(self):

        snapshots = snapshot_manager.all()

        results = []

        for symbol, snapshot in snapshots.items():

            snapshot = self.indicators.analyze(snapshot)

            snapshot = self.scoring.score(snapshot)

            results.append(snapshot)

        return self.ranking.sort(results)