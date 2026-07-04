"""
OAMI Enterprise
OpenAlgo WebSocket Live Quote Test
"""

import time

from app.openalgo.websocket import OpenAlgoWebSocket
from app.services.snapshot_manager import SnapshotManager


# ------------------------------------------------------------------
# Snapshot Manager
# ------------------------------------------------------------------

snapshot_manager = SnapshotManager()


# ------------------------------------------------------------------
# Quote Callback
# ------------------------------------------------------------------

def on_quote(data):
    """
    Called whenever OpenAlgo receives a live quote.
    """

    snapshot_manager.update_quote(data)

    snapshot = snapshot_manager.get(data["symbol"])

    print("\n" + "=" * 60)
    print(f"Symbol : {snapshot.symbol}")
    print(f"LTP    : {snapshot.ltp}")
    print(f"Open   : {snapshot.open}")
    print(f"High   : {snapshot.high}")
    print(f"Low    : {snapshot.low}")
    print(f"Close  : {snapshot.close}")
    print(f"Volume : {snapshot.volume}")
    print("=" * 60)


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

print("=" * 60)
print("OAMI LIVE MARKET SNAPSHOT TEST")
print("=" * 60)

ws = OpenAlgoWebSocket()

connected = ws.connect()

print(f"Connect returned : {connected}")

if connected:

    instruments = [
        {"exchange": "NSE", "symbol": "RELIANCE"},
        {"exchange": "NSE", "symbol": "SBIN"},
        {"exchange": "NSE", "symbol": "INFY"},
        {"exchange": "NSE", "symbol": "TCS"},
        {"exchange": "NSE", "symbol": "HDFCBANK"},
    ]

    print("\nSubscribing...")

    try:

        result = ws.client.subscribe_quote(
            instruments=instruments,
            on_data_received=on_quote,
        )

        print(f"Subscription Result : {result}")

    except Exception as e:

        print(f"Subscription Error : {e}")

    print("\nWaiting for live market data...\n")

    try:

        while True:
            time.sleep(1)

    except KeyboardInterrupt:

        print("\nDisconnecting...")

        ws.disconnect()

else:

    print("WebSocket connection failed.")