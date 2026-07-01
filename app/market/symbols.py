"""
OAMI Enterprise
Market Symbol Manager
"""

from pathlib import Path


class SymbolManager:
    """Loads and manages watchlists."""

    def __init__(self, watchlist_name: str = "custom"):
        self.watchlist_name = watchlist_name
        self.symbols = []

    def load(self):
        """Load symbols from the selected watchlist."""

        file_path = Path("config") / "watchlists" / f"{self.watchlist_name}.txt"

        if not file_path.exists():
            raise FileNotFoundError(f"Watchlist not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as file:
            self.symbols = [
                line.strip().upper()
                for line in file
                if line.strip()
            ]

        # Remove duplicates while preserving order
        self.symbols = list(dict.fromkeys(self.symbols))

        return self.symbols

    def count(self):
        """Return number of loaded symbols."""
        return len(self.symbols)

    def show(self):
        """Display loaded symbols."""
        print(f"Loaded {self.count()} symbols")

        for symbol in self.symbols:
            print(symbol)