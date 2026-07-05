"""
OAMI Enterprise
Application Controller
"""

import time

from app.openalgo.websocket import OpenAlgoWebSocket
from app.market.scanner import Scanner
from app.services.watchlist_manager import watchlist


class OAMIApplication:

    def __init__(self):

        self.websocket = OpenAlgoWebSocket()
        self.scanner = Scanner()

    def start(self):

        # Initial Watchlist
        watchlist.set_symbols([
            "RELIANCE",
            "SBIN",
            "INFY",
            "TCS",
            "HDFCBANK",
        ])

        # Start WebSocket
        if not self.websocket.start():
            print("Failed to start WebSocket.")
            return

        print("\n✅ OAMI Started Successfully\n")

        try:

            while True:

                results = self.scanner.scan()

                print("\n" + "=" * 120)
                print("LIVE MARKET SCANNER")
                print("=" * 120)

                if not results:
                    print("Waiting for market data...")

                else:

                    for rank, snapshot in enumerate(results, start=1):

                        print(
                            f"{rank:02d}. "
                            f"{snapshot.symbol:<12}"
                            f"LTP={snapshot.ltp:>8.2f} "
                            f"Open={snapshot.open:>8.2f} "
                            f"Close={snapshot.close:>8.2f} "
                            f"Chg={snapshot.change_pct:>7.2f}% "
                            f"Trend={snapshot.trend:<8} "
                            f"Mom={snapshot.momentum:<8} "
                            f"Score={snapshot.score:<3} "
                            f"Conf={snapshot.confidence:<3}"
                        )

                time.sleep(5)

        except KeyboardInterrupt:

            print("\nStopping OAMI...")

            self.websocket.disconnect()

            print("OAMI stopped successfully.")