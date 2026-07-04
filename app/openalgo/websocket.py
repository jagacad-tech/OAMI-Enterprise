"""
OAMI Enterprise
OpenAlgo WebSocket Manager
"""

from openalgo import api
from app.core.config import settings


class OpenAlgoWebSocket:

    def __init__(self):

        self.client = api(
            api_key=settings.openalgo["api_key"],
            host=settings.openalgo["host"],
            ws_url=settings.openalgo["websocket_url"],
            timeout=settings.openalgo["timeout"],
            verbose=2,
        )

    def connect(self):
        """
        Connect WebSocket
        """
        connected = self.client.connect()

        if connected:
            print("✓ Connected")

        return connected

    def disconnect(self):
        self.client.disconnect()
        print("Disconnected")