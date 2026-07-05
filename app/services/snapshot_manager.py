from app.market.models import MarketSnapshot


class SnapshotManager:

    def __init__(self):
        self.snapshots = {}

    def update_quote(self, quote):

        symbol = quote["symbol"]
        data = quote["data"]

        self.snapshots[symbol] = MarketSnapshot(
            symbol=symbol,
            status="LIVE",
            ltp=data.get("ltp"),
            open=data.get("open"),
            high=data.get("high"),
            low=data.get("low"),
            close=data.get("close"),
            volume=data.get("volume"),
            trend=None,
            score=0,
        )

    def get(self, symbol):
        return self.snapshots.get(symbol)

    def all(self):
        return self.snapshots.copy()
    
snapshot_manager = SnapshotManager()