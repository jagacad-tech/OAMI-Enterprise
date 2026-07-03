"""
OAMI Enterprise
Ranking Engine
"""

from app.market.models import MarketSnapshot


class RankingEngine:
    """
    Sorts market opportunities by score.
    """

    def rank(
        self,
        snapshots: list[MarketSnapshot]
    ) -> list[MarketSnapshot]:

        return sorted(
            snapshots,
            key=lambda snapshot: snapshot.score,
            reverse=True,
        )