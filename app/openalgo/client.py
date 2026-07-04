from openalgo import api
from app.core.config import settings


class OpenAlgoClient:

    def __init__(self):

        self.client = api(
            api_key=settings.openalgo["api_key"],
            host=settings.openalgo["host"],
            timeout=settings.openalgo["timeout"],
            verbose=False,
        )

    # ------------------------
    # Account
    # ------------------------

    def get_funds(self):
        return self.client.funds()

    def get_holdings(self):
        return self.client.holdings()

    def get_positions(self):
        return self.client.positionbook()

    def get_orders(self):
        return self.client.orderbook()

    def get_trades(self):
        return self.client.tradebook()

    # ------------------------
    # Market Data
    # ------------------------

    def get_ltp(self, exchange, symbol):
        return self.client.get_ltp(
            exchange=exchange,
            symbol=symbol
        )

    def get_quotes(self, exchange, symbol):
        return self.client.get_quotes(
            exchange=exchange,
            symbol=symbol
        )

    def get_history(self, **kwargs):
        return self.client.history(**kwargs)

    # ------------------------
    # Trading
    # ------------------------

    def place_order(self, **kwargs):
        return self.client.placeorder(**kwargs)