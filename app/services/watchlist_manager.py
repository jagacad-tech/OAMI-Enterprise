"""
OAMI Enterprise
Watchlist Manager
"""

from typing import List


class WatchlistManager:

    def __init__(self):
        self._symbols = []

    def set_symbols(self, symbols: List[str]):
        self._symbols = list(dict.fromkeys(symbols))

    def add(self, symbol: str):
        if symbol not in self._symbols:
            self._symbols.append(symbol)

    def remove(self, symbol: str):
        if symbol in self._symbols:
            self._symbols.remove(symbol)

    def clear(self):
        self._symbols.clear()

    def symbols(self):
        return self._symbols.copy()

    def websocket_instruments(self):
        """
        Build OpenAlgo subscription instruments with the correct exchange.
        """

        nse_indices = {
            "NIFTY",
            "BANKNIFTY",
            "FINNIFTY",
            "MIDCPNIFTY",
            "INDIAVIX",
        }

        bse_indices = {
            "SENSEX",
            "BANKEX",
        }

        instruments = []

        for symbol in self._symbols:

            if symbol in nse_indices:

                exchange = "NSE_INDEX"

            elif symbol in bse_indices:

                exchange = "BSE_INDEX"

            else:

                exchange = "NSE"

            instruments.append(
                {
                    "exchange": exchange,
                    "symbol": symbol,
                }
            )

        return instruments


# --------------------------------------------------------
# Global Singleton
# --------------------------------------------------------

watchlist = WatchlistManager()