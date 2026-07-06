import json
import time

from app.openalgo.websocket import OpenAlgoWebSocket
from app.services.watchlist_manager import watchlist


watchlist.set_symbols([
    "RELIANCE",
])


def on_depth(data):

    print("=" * 80)
    print(json.dumps(data, indent=4))
    print("=" * 80)


ws = OpenAlgoWebSocket()

if ws.connect():

    ws.client.subscribe_depth(
        instruments=watchlist.websocket_instruments(),
        on_data_received=on_depth,
    )

    print("Waiting for depth data...")

    while True:
        time.sleep(1)