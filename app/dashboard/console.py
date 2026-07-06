"""
OAMI Enterprise
Console Dashboard
"""

import os
from datetime import datetime
MARKET_STATE_LABELS = {
    "TRENDING_BULL": "🟢 TRENDING BULL",
    "TRENDING_BEAR": "🔴 TRENDING BEAR",
    "SIDEWAYS": "🟡 SIDEWAYS",
    "HIGH_ACTIVITY": "🟣 HIGH ACTIVITY",
    "UNKNOWN": "⚪ UNKNOWN",
}


class ConsoleDashboard:

    def show(self, snapshots, market):

        # Clear terminal
        os.system("cls" if os.name == "nt" else "clear")

        print("=" * 130)
        print("                                         OAMI ENTERPRISE - LIVE MARKET DASHBOARD")
        print("=" * 130)

        print(f"Time           : {datetime.now().strftime('%H:%M:%S')}")
        print(f"Symbols        : {len(snapshots)}")
        #print(f"Market State   : {market['state']}")
        print(
            f"Market State   : "
            f"{MARKET_STATE_LABELS.get(market['state'], market['state'])}"
        )
        print(f"Average Score  : {market['avg_score']}")
        print(f"Average RVOL   : {market['avg_rvol']}")

        print(
            f"Bullish : {market['bullish']}    "
            f"Bearish : {market['bearish']}    "
            f"Neutral : {market['neutral']}"
        )

        print()

        print("-" * 132)

        print(
            f"{'Rank':<6}"
            f"{'Symbol':<15}"
            f"{'LTP':>10}"
            f"{'Open':>10}"
            f"{'Change%':>12}"
            f"{'RVOL':>8}"
            f"{'Pos%':>10}"
            f"{'Trend':>12}"
            f"{'Momentum':>12}"
            f"{'Score':>8}"
            f"{'Direction':>12}"
            f"{'Signal':>10}"
            f"{'Option':>8}"
            f"{'Strategy':>12}"
            f"{'Action':>12}"
            f"{'Quality':>10}"
            f"{'Strength':>10}"
            f"{'Conf':>8}"
        )

        print("-" * 132)

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
                f"{snapshot.rvol:>8.2f}"
                f"{snapshot.intraday_position:>10.1f}"
                f"{snapshot.trend:>12}"
                f"{snapshot.momentum:>12}"
                f"{snapshot.score:>8}"
                f"{snapshot.direction:>12}"
                f"{snapshot.signal:>10}"
                f"{snapshot.option_type:>8}"
                f"{snapshot.strategy:>12}"
                f"{snapshot.action:>12}"
                f"{snapshot.setup_quality:>10}"
                f"{snapshot.signal_strength:>10}"
                f"{snapshot.confidence:>8}"
            )

        print("-" * 132)