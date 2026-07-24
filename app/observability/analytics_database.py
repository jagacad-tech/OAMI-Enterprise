"""SQLite schema shared by OAMI's passive analytics writers."""

import sqlite3
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS trade_intelligence_trades (
    trade_id TEXT PRIMARY KEY,
    version TEXT NOT NULL,
    symbol TEXT NOT NULL,
    option_type TEXT NOT NULL,
    entered_at TEXT NOT NULL,
    confirmed_at TEXT,
    exited_at TEXT,
    exit_reason TEXT,
    entry_snapshot_json TEXT NOT NULL,
    exit_snapshot_json TEXT,
    valid_exit TEXT NOT NULL DEFAULT '',
    early_exit TEXT NOT NULL DEFAULT '',
    late_exit TEXT NOT NULL DEFAULT '',
    perfect_exit TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS trade_lifecycle_transitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id TEXT NOT NULL,
    transition_at TEXT NOT NULL,
    scan_id INTEGER NOT NULL,
    from_state TEXT NOT NULL,
    to_state TEXT NOT NULL,
    lifecycle_reason TEXT NOT NULL,
    snapshot_json TEXT,
    fingerprint_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_trade_transitions_trade_id
    ON trade_lifecycle_transitions(trade_id, transition_at);

CREATE TABLE IF NOT EXISTS trade_post_exit_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_id TEXT NOT NULL,
    offset_minutes INTEGER NOT NULL,
    scheduled_at TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    underlying_snapshot_json TEXT,
    option_symbol TEXT,
    option_snapshot_json TEXT,
    option_snapshot_status TEXT NOT NULL,
    UNIQUE(trade_id, offset_minutes)
);

CREATE TABLE IF NOT EXISTS market_session_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    captured_at TEXT NOT NULL,
    market_timestamp TEXT,
    symbol TEXT NOT NULL,
    exchange TEXT NOT NULL,
    ltp REAL NOT NULL,
    trend TEXT NOT NULL,
    momentum TEXT NOT NULL,
    rvol REAL NOT NULL,
    bid_pressure INTEGER NOT NULL,
    ask_pressure INTEGER NOT NULL,
    orderbook_imbalance REAL NOT NULL,
    spread REAL NOT NULL,
    score INTEGER NOT NULL,
    confidence INTEGER NOT NULL,
    snapshot_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_market_session_symbol_time
    ON market_session_snapshots(symbol, captured_at);
"""


# Version 2 is deliberately additive: existing analytics tables and queries
# remain unchanged while unfinished post-exit work becomes durable.
MIGRATION_2 = """
CREATE TABLE IF NOT EXISTS analytics_schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS trade_post_exit_schedule (
    trade_id TEXT NOT NULL,
    offset_minutes INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    option_symbol TEXT NOT NULL DEFAULT '',
    scheduled_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    PRIMARY KEY (trade_id, offset_minutes)
);
CREATE INDEX IF NOT EXISTS idx_trade_post_exit_schedule_due
    ON trade_post_exit_schedule(completed_at, scheduled_at);

-- Backfill any post-exit offset not present in the legacy snapshot table.
-- INSERT OR IGNORE makes this safe to run repeatedly and preserves existing
-- completed snapshots without replacing them.
INSERT OR IGNORE INTO trade_post_exit_schedule (
    trade_id, offset_minutes, symbol, option_symbol, scheduled_at, created_at
)
SELECT
    trade.trade_id,
    offsets.offset_minutes,
    trade.symbol,
    '',
    datetime(trade.exited_at, '+' || offsets.offset_minutes || ' minutes'),
    trade.exited_at
FROM trade_intelligence_trades AS trade
CROSS JOIN (
    SELECT 1 AS offset_minutes
    UNION ALL SELECT 2
    UNION ALL SELECT 3
    UNION ALL SELECT 5
    UNION ALL SELECT 10
) AS offsets
LEFT JOIN trade_post_exit_snapshots AS snapshot
    ON snapshot.trade_id = trade.trade_id
    AND snapshot.offset_minutes = offsets.offset_minutes
WHERE trade.exited_at IS NOT NULL
  AND snapshot.id IS NULL;

INSERT OR IGNORE INTO analytics_schema_migrations (version, applied_at)
VALUES (2, strftime('%Y-%m-%dT%H:%M:%f', 'now'));
"""


def connect(path):
    """Open a writer connection with a schema suitable for independent workers."""
    database_path = Path(path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=10)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA busy_timeout=10000")
    connection.executescript(SCHEMA)
    connection.executescript(MIGRATION_2)
    connection.commit()
    return connection
