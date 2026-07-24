import unittest
from pathlib import Path
from uuid import uuid4

from app.dashboard.market_indices import MarketIndexFeed
from app.market.models import MarketSnapshot
from app.observability.analytics_database import connect
from app.observability.market_session import MarketSessionRecorder


class MarketIndexDashboardTests(unittest.TestCase):
    def test_returns_only_the_latest_value_and_trend_per_index(self):
        path = Path("data") / f"dashboard-index-test-{uuid4().hex}.sqlite3"
        try:
            connection = connect(path)
            try:
                MarketSessionRecorder._persist(
                    connection,
                    MarketSnapshot(symbol="NIFTY", ltp=22000.0, trend="BULLISH"),
                )
                MarketSessionRecorder._persist(
                    connection,
                    MarketSnapshot(symbol="NIFTY", ltp=22100.0, trend="BEARISH"),
                )
                MarketSessionRecorder._persist(
                    connection,
                    MarketSnapshot(symbol="SENSEX", ltp=73000.0, trend="NEUTRAL"),
                )
                connection.commit()
            finally:
                connection.close()

            indices = MarketIndexFeed(path).latest()

            self.assertEqual(
                indices,
                [
                    {"symbol": "NIFTY", "value": 22100.0, "trend": "BEARISH"},
                    {"symbol": "SENSEX", "value": 73000.0, "trend": "NEUTRAL"},
                ],
            )
        finally:
            for candidate in (path, Path(f"{path}-wal"), Path(f"{path}-shm")):
                candidate.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
