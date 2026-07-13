from openalgo import api
from app.core.config import settings

client = api(
    api_key=settings.openalgo["api_key"],
    host=settings.openalgo["host"],
    ws_url=settings.openalgo["websocket_url"],
)

symbols = [
    {"exchange": "NSE_INDEX", "symbol": "NIFTY"},
    {"exchange": "NSE_INDEX", "symbol": "BANKNIFTY"},
    {"exchange": "NSE_INDEX", "symbol": "FINNIFTY"},
    {"exchange": "BSE_INDEX", "symbol": "SENSEX"},
]

def on_data(data):
    print(data)

print("Connecting...")

client.connect()

print("Subscribing...")

client.subscribe_quote(
    instruments=symbols,
    on_data_received=on_data,
)

input("Waiting for quotes... Press Enter to exit.")