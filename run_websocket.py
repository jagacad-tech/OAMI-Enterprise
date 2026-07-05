"""
OAMI Enterprise
Production WebSocket Verification
"""

import time

from app.openalgo.websocket import OpenAlgoWebSocket
from app.services.watchlist_manager import watchlist
from app.services.snapshot_manager import snapshot_manager


# ----------------------------------------------------
# Configure Watchlist
# ----------------------------------------------------

watchlist.set_symbols([
    "RELIANCE",
    "SBIN",
    "INFY",
    "TCS",
    "HDFCBANK",
])

# ----------------------------------------------------
# Start WebSocket
# ----------------------------------------------------

ws = OpenAlgoWebSocket()

if ws.start():

    print("\n✅ OAMI Production WebSocket Started\n")

    try:

        while True:

            print("\n================ SNAPSHOTS ================\n")

            snapshots = snapshot_manager.all()

            if not snapshots:
                print("No snapshots received yet...")

            for symbol, snapshot in snapshots.items():

                print(
                    f"{symbol:<12}"
                    f"LTP={snapshot.ltp:<10}"
                    f"VOL={snapshot.volume}"
                )

            time.sleep(5)

    except KeyboardInterrupt:

        print("\nStopping...")

        ws.disconnect()

else:

    print("Failed to start WebSocket.")