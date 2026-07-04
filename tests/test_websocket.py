from app.openalgo.websocket import OpenAlgoWebSocket

print("="*60)
print("OPENALGO WEBSOCKET TEST")
print("="*60)

ws = OpenAlgoWebSocket()

ws.connect()

input("\nPress ENTER to disconnect...")

ws.disconnect()