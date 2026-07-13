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
from pathlib import Path


class OAMIApplication:

    def __init__(self):

        self.websocket = OpenAlgoWebSocket()
        self.scanner = Scanner()
        self.dashboard = ConsoleDashboard()
        self.market_state = MarketStateEngine()

    def start(self):

        # ----------------------------------------
        # Load Watchlist from config/watchlists/custom.txt
        # ----------------------------------------

        watchlist_file = Path("config/watchlists/custom.txt")

        symbols = []

        with open(watchlist_file, "r", encoding="utf-8") as f:
            for line in f:
                symbol = line.strip().upper()
                if symbol:
                    symbols.append(symbol)

        watchlist.set_symbols(symbols)

        print(f"Loaded {len(symbols)} symbols:")
        for symbol in symbols:
            print(f"  - {symbol}")
            

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