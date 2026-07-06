"""
OAMI Enterprise
Application Controller
"""

import time

from app.openalgo.websocket import OpenAlgoWebSocket
from app.market.scanner import Scanner
from app.services.watchlist_manager import watchlist
from app.dashboard.console import ConsoleDashboard
from app.market.market_state import MarketStateEngine


class OAMIApplication:

    def __init__(self):

        self.websocket = OpenAlgoWebSocket()
        self.scanner = Scanner()
        self.dashboard = ConsoleDashboard()
        self.market_state = MarketStateEngine()

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
                
                market = self.market_state.analyze(results)
                                             
                self.dashboard.show(results, market)
               
                time.sleep(5)

        except Exception as e:

            print("\nAPPLICATION ERROR")
            print("=================")
            print(e)

        except KeyboardInterrupt:

            print("\nStopping OAMI...")

            self.websocket.disconnect()

            print("OAMI stopped successfully.")