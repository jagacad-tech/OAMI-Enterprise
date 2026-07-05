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

        while True:

            results = self.scanner.scan()

            print("\n================ LIVE RANKING ================\n")

            for i, snapshot in enumerate(results, start=1):

                print(
                    f"{i:02d}. "
                    f"{snapshot.symbol:<12}"
                    f"Score={snapshot.score:<3}"
                    f"Trend={snapshot.trend}"
                    f"  LTP={snapshot.ltp}"
                )

            time.sleep(5)