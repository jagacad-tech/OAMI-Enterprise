"""
OAMI Enterprise
OpenAlgo WebSocket Manager

Responsibilities:
- Connect to OpenAlgo WebSocket
- Subscribe to live market feeds
- Update SnapshotManager
- Hide OpenAlgo implementation from the rest of OAMI
"""

from openalgo import api

from app.core.config import settings
from app.services.watchlist_manager import watchlist
from app.services.snapshot_manager import snapshot_manager


# ---------------------------------------------------------
# Debug Flags
# ---------------------------------------------------------

DEBUG_CALLBACK = True
DEBUG_SUBSCRIPTION = True


class OpenAlgoWebSocket:
    """
    Production WebSocket Manager
    """

    def __init__(self):

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

            snapshot_manager.update_quote(data)

            snapshot = snapshot_manager.get(data["symbol"])

            # ----------------------------------------
            # Debug Callback
            # ----------------------------------------

            if DEBUG_CALLBACK:

                print(
                    f"QUOTE RECEIVED : "
                    f"{snapshot.symbol:<12}"
                    f"LTP={snapshot.ltp}"
                )

            return snapshot

        except Exception as e:

            print("\n==============================")
            print("CALLBACK ERROR")
            print("==============================")
            print(e)
            print(data)
            print("==============================")

    # ---------------------------------------------------------
    # Quote Subscription
    # ---------------------------------------------------------

    def subscribe_quotes(self):

        if not watchlist.symbols():

            print("Watchlist is empty.")

            return False

        print(
            f"Subscribing {len(watchlist.symbols())} symbols..."
        )

        # ----------------------------------------
        # Debug Subscription
        # ----------------------------------------

        if DEBUG_SUBSCRIPTION:

            print("\n====================================")
            print("SUBSCRIBING INSTRUMENTS")
            print("====================================")

            for instrument in watchlist.websocket_instruments():

                print(instrument)

            print("====================================\n")

        return self.client.subscribe_quote(
            instruments=watchlist.websocket_instruments(),
            on_data_received=self.on_quote,
        )

    # ---------------------------------------------------------
    # Future Features
    # ---------------------------------------------------------

    def subscribe_depth(self):
        """
        Reserved for Level-5 Order Book
        """
        pass

    def subscribe_ltp(self):
        """
        Reserved for lightweight LTP stream
        """
        pass

    # ---------------------------------------------------------
    # Start Service
    # ---------------------------------------------------------

    def start(self):

        if not self.connect():
            return False

        return self.subscribe_quotes()