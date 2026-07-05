"""
OAMI Enterprise
Ranking Engine
"""


class RankingEngine:

    def sort(self, snapshots):

        return sorted(
            snapshots,
            key=lambda x: x.score,
            reverse=True
        )