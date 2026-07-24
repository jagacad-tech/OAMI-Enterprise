"""
OAMI Enterprise
OpenAlgo WebSocket Manager

Responsibilities:
- Connect to OpenAlgo WebSocket
- Subscribe to Quote feed
- Subscribe to Depth feed
- Update SnapshotManager
"""

from openalgo import api

from app.core.config import settings
from app.core.logger import logger
from app.observability.market_session import MarketSessionRecorder
from app.services.watchlist_manager import watchlist
from app.services.snapshot_manager import snapshot_manager


# ---------------------------------------------------------
# Debug Flags
# ---------------------------------------------------------

DEBUG_WEBSOCKET = False
DEBUG_SUBSCRIPTION = True


class OpenAlgoWebSocket:
    """
    Production WebSocket Manager
    """

    def __init__(self, market_session_recorder=None):

        self.market_session_recorder = market_session_recorder

        self.client = api(
            api_key=settings.openalgo["api_key"],
            host=settings.openalgo["host"],
            ws_url=settings.openalgo["websocket_url"],
            timeout=settings.openalgo["timeout"],
            verbose=settings.openalgo.get("verbose", 0),
        )

    # ---------------------------------------------------------
    # Connection
    # ---------------------------------------------------------

    def connect(self) -> bool:

        connected = self.client.connect()

        if connected:
            print("✓ Connected")

        return connected

    def disconnect(self):

        self.client.disconnect()

        print("Disconnected")

    # ---------------------------------------------------------
    # Quote Callback
    # ---------------------------------------------------------

    def on_quote(self, data):

        try:

            # Index updates belong to the passive market-session analytics
            # stream.  They deliberately never enter the stock snapshot store,
            # so the stock scanner cannot create index signals or lifecycles.
            if MarketSessionRecorder.accepts(data):
                if self.market_session_recorder is not None:
                    self.market_session_recorder.observe(data)
                return None

            # ----------------------------------------
            # DEBUG
            # ----------------------------------------

            if DEBUG_WEBSOCKET:
                payload = data.get("data", {})
                logger.debug(
                    "WebSocket callback: symbol=%s mode=%s depth=%s data_keys=%s",
                    data.get("symbol"),
                    data.get("mode"),
                    "depth" in payload,
                    list(payload.keys()),
                )

            if data.get("mode") == 2:
                snapshot_manager.update_quote(data)

            elif data.get("mode") == 3:
                snapshot_manager.update_depth(data)

            return snapshot_manager.get(data["symbol"])

        except Exception:

            logger.exception("OpenAlgo quote callback failed")

            print("\n==============================")
            print("CALLBACK ERROR")
            print("==============================")
            print(data)
            print("==============================")

            return None

    # ---------------------------------------------------------
    # Quote Subscription
    # ---------------------------------------------------------

    def subscribe_quotes(self):

        if not watchlist.symbols():

            print("Watchlist is empty.")

            return False

        print(
            f"Subscribing Quotes for {len(watchlist.symbols())} symbols..."
        )

        if DEBUG_SUBSCRIPTION:

            print("\n====================================")
            print("QUOTE SUBSCRIPTION")
            print("====================================")

            for instrument in watchlist.websocket_instruments():
                print(instrument)

            print("====================================\n")

        return self.client.subscribe_quote(
            instruments=watchlist.websocket_instruments(),
            on_data_received=self.on_quote,
        )

    # ---------------------------------------------------------
    # Depth Subscription
    # ---------------------------------------------------------

    def subscribe_depth(self):

        if not watchlist.symbols():

            print("Watchlist is empty.")

            return False

        print(
            f"Subscribing Depth for {len(watchlist.symbols())} symbols..."
        )

        return self.client.subscribe_depth(
            instruments=watchlist.websocket_instruments(),
            on_data_received=self.on_quote,
        )

    # ---------------------------------------------------------
    # Future
    # ---------------------------------------------------------

    def subscribe_ltp(self):
        """
        Reserved for lightweight LTP stream
        """
        pass

    # ---------------------------------------------------------
    # Start
    # ---------------------------------------------------------

    def start(self):

        if not self.connect():
            return False

        quote_ok = self.subscribe_quotes()

        depth_ok = self.subscribe_depth()

        if quote_ok:
            print("✓ Quote subscription successful")
        else:
            print("✗ Quote subscription failed")

        if depth_ok:
            print("✓ Depth subscription successful")
        else:
            print("✗ Depth subscription failed")

        return quote_ok and depth_ok
