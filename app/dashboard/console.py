"""
OAMI Enterprise
Console Dashboard
"""

import os
from datetime import datetime


class ConsoleDashboard:

    def show(self, snapshots):

        # Clear terminal
        os.system("cls" if os.name == "nt" else "clear")

        print("=" * 110)
        print("                 OAMI ENTERPRISE - LIVE MARKET DASHBOARD")
        print("=" * 110)

        print(
            f"Time : {datetime.now().strftime('%H:%M:%S')}"
        )

        print(
            f"Symbols : {len(snapshots)}"
        )

        bullish = sum(
            1 for s in snapshots if s.trend == "BULLISH"
        )

        bearish = sum(
            1 for s in snapshots if s.trend == "BEARISH"
        )

        neutral = len(snapshots) - bullish - bearish

        print(
            f"Bullish : {bullish}    "
            f"Bearish : {bearish}    "
            f"Neutral : {neutral}"
        )

        print()

        print("-" * 110)

        print(
            f"{'Rank':<6}"
            f"{'Symbol':<15}"
            f"{'LTP':>10}"
            f"{'Open':>10}"
            f"{'Change%':>12}"
            f"{'Pos%':>10}"
            f"{'Trend':>12}"
            f"{'Momentum':>12}"
            f"{'Score':>8}"
            f"{'Conf':>8}"
        )

        print("-" * 110)

        if not snapshots:

            print("Waiting for market data...")

            return

        for rank, snapshot in enumerate(snapshots, start=1):

            print(
                f"{rank:<6}"
                f"{snapshot.symbol:<15}"
                f"{snapshot.ltp:>10.2f}"
                f"{snapshot.open:>10.2f}"
                f"{snapshot.change_pct:>12.2f}"
                f"{snapshot.intraday_position:>10.1f}"
                f"{snapshot.trend:>12}"
                f"{snapshot.momentum:>12}"
                f"{snapshot.score:>8}"
                f"{snapshot.confidence:>8}"
            )

        print("-" * 110)