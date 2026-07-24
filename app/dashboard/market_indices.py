"""Read-only market-index feed for the web dashboard."""

import sqlite3
from pathlib import Path

from app.market.indexes import INDEX_DISPLAY_ORDER


class MarketIndexFeed:
    """Return the most recent passive snapshot for each supported index.

    This reader intentionally uses only the market-session store.  It does
    not read scanner results or invoke any market, scoring, signal, or trade
    components.
    """

    def __init__(self, database_path):
        self.database_path = Path(database_path)

    def latest(self):
        """Return one display-safe value and trend for each available index."""
        if not self.database_path.exists():
            return []

        placeholders = ", ".join("?" for _ in INDEX_DISPLAY_ORDER)
        ordering = " ".join(
            f"WHEN ? THEN {position}"
            for position in range(len(INDEX_DISPLAY_ORDER))
        )
        query = f"""
            SELECT snapshot.symbol, snapshot.ltp, snapshot.trend
            FROM market_session_snapshots AS snapshot
            INNER JOIN (
                SELECT symbol, MAX(id) AS latest_id
                FROM market_session_snapshots
                WHERE symbol IN ({placeholders})
                GROUP BY symbol
            ) AS latest ON snapshot.id = latest.latest_id
            ORDER BY CASE snapshot.symbol {ordering} ELSE {len(INDEX_DISPLAY_ORDER)} END
        """
        parameters = (*INDEX_DISPLAY_ORDER, *INDEX_DISPLAY_ORDER)

        try:
            connection = sqlite3.connect(self.database_path)
            try:
                rows = connection.execute(query, parameters).fetchall()
            finally:
                connection.close()
        except sqlite3.Error:
            # The dashboard remains available while the passive writer is
            # initializing or its database is temporarily unavailable.
            return []

        return [
            {
                "symbol": symbol,
                "value": ltp,
                "trend": trend,
            }
            for symbol, ltp, trend in rows
        ]
