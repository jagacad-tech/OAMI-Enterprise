"""
OAMI Enterprise
Application Controller
"""

import time

from app.openalgo.websocket import OpenAlgoWebSocket
from app.market.scanner import Scanner
from app.market.scanner_service import ScannerService
from app.services.watchlist_manager import watchlist
from app.dashboard.console import ConsoleDashboard
from app.market.market_state import MarketStateEngine
from app.services.snapshot_manager import snapshot_manager
from app.core.logger import logger
from app.observability.factory import build_market_session_recorder
from pathlib import Path


class OAMIApplication:

    def __init__(self):

        self.market_session_recorder = build_market_session_recorder()
        self.websocket = OpenAlgoWebSocket(self.market_session_recorder)
        self.scanner = Scanner()
        self.scanner_service = ScannerService(
            self.scanner,
            on_scan_completed=self._handle_scan_completed,
        )
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
            if self.market_session_recorder is not None:
                self.market_session_recorder.close()
            return

        print("\n✅ OAMI Started Successfully\n")

        if not self.scanner_service.start():
            logger.error("OAMI startup aborted because the scanner service did not start")
            self.websocket.disconnect()
            if self.market_session_recorder is not None:
                self.market_session_recorder.close()
            return

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping OAMI...")
        except Exception:
            # The scanner itself is separately protected.  This boundary keeps
            # an unexpected main-thread error from skipping shutdown.
            logger.exception("Application main loop failed")
        finally:
            self.scanner_service.stop()
            self.scanner.lifecycle_events.close()
            self.websocket.disconnect()
            if self.market_session_recorder is not None:
                self.market_session_recorder.close()
            print("OAMI stopped successfully.")

    def _handle_scan_completed(self, results):
        """Render post-scan diagnostics without participating in scan logic."""
        market = self.market_state.analyze(results)

        active_snapshots = snapshot_manager.all()
        diagnostics = {
            "configured_watchlist_symbols": len(watchlist.symbols()),
            "active_snapshots": len(active_snapshots),
            "quote_feed_status": self.feed_status(
                active_snapshots.values(), "quote_updated_at"
            ),
            "depth_feed_status": self.feed_status(
                active_snapshots.values(), "depth_updated_at"
            ),
            "lifecycle_event_count": self.scanner.lifecycle_events.event_count,
            "scanner": self.scanner_service.status(),
        }

        self.dashboard.show(results, market, diagnostics)

    @staticmethod
    def feed_status(snapshots, updated_attribute):
        return "ACTIVE" if any(
            getattr(snapshot, updated_attribute) is not None
            for snapshot in snapshots
        ) else "WAITING"
