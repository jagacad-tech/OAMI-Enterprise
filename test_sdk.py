from app.openalgo.websocket import OpenAlgoWebSocket
import inspect

ws = OpenAlgoWebSocket()

print(inspect.signature(ws.client.subscribe_depth))