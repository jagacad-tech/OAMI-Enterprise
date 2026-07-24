import sqlite3
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from threading import Event
from unittest.mock import patch
from uuid import uuid4

from app.core.constants import APP_VERSION
from app.market.models import MarketSnapshot
from app.observability.lifecycle_events import LifecycleTransitionEvent, SnapshotFingerprint
from app.observability.analytics_database import SCHEMA, connect
from app.observability.market_session import MarketSessionRecorder
from app.observability.trade_intelligence import TradeIntelligenceLogger
from app.openalgo.websocket import OpenAlgoWebSocket
from app.services.snapshot_manager import snapshot_manager


def lifecycle_event(trade_id, to_state, reason, timestamp=None):
    now = timestamp or datetime.now()
    return LifecycleTransitionEvent(
        version=APP_VERSION,
        scan_id=1,
        timestamp=now,
        trade_id=trade_id,
        symbol="ANALYTICS_TEST",
        option_type="CE",
        from_state="CONFIRMED" if to_state == "EXIT" else "INVALID",
        to_state=to_state,
        lifecycle_reason=reason,
        trade_started_at=now,
        confirmed_at=None,
        fingerprint=SnapshotFingerprint(
            ltp=100.0,
            score=75,
            confidence=75,
            trend="BULLISH",
            momentum="MEDIUM",
            rvol=1.5,
            obi=0.2,
            bid_pressure=200,
            ask_pressure=100,
            spread=0.05,
            lifecycle_reason=reason,
        ),
    )


class AnalyticsObservabilityTests(unittest.TestCase):
    def test_trade_intelligence_records_entry_exit_and_blank_classifications(self):
        path = Path("data") / f"analytics-test-{uuid4().hex}.sqlite3"
        try:
            trade_id = "T-ANALYTICS-TEST"
            snapshot_manager.snapshots["ANALYTICS_TEST"] = MarketSnapshot(
                symbol="ANALYTICS_TEST",
                ltp=100.0,
                score=75,
                confidence=75,
                trend="BULLISH",
                momentum="MEDIUM",
                rvol=1.5,
            )
            recorder = TradeIntelligenceLogger(path)
            try:
                recorder(lifecycle_event(trade_id, "NEW BUY", "Entry"))
                recorder(lifecycle_event(trade_id, "EXIT", "Exit"))
                recorder._queue.join()
                connection = sqlite3.connect(path)
                try:
                    scheduled = connection.execute(
                        "SELECT COUNT(*) FROM trade_post_exit_schedule WHERE trade_id = ?",
                        (trade_id,),
                    ).fetchone()[0]
                finally:
                    connection.close()
                self.assertEqual(scheduled, 5)
            finally:
                recorder.close()

            connection = sqlite3.connect(path)
            try:
                trade = connection.execute(
                    "SELECT exit_reason, valid_exit, early_exit, late_exit, perfect_exit "
                    "FROM trade_intelligence_trades WHERE trade_id = ?",
                    (trade_id,),
                ).fetchone()
                transitions = connection.execute(
                    "SELECT COUNT(*) FROM trade_lifecycle_transitions WHERE trade_id = ?",
                    (trade_id,),
                ).fetchone()[0]
            finally:
                connection.close()
            self.assertEqual(trade, ("Exit", "", "", "", ""))
            self.assertEqual(transitions, 2)
        finally:
            self._remove_database(path)

    def test_post_exit_schedule_recovers_after_writer_restart(self):
        path = Path("data") / f"analytics-test-{uuid4().hex}.sqlite3"
        trade_id = f"T-ANALYTICS-RECOVERY-{uuid4().hex}"
        exited_at = datetime.now() - timedelta(minutes=11)
        snapshot_manager.snapshots["ANALYTICS_TEST"] = MarketSnapshot(
            symbol="ANALYTICS_TEST", ltp=101.0
        )
        try:
            # Simulate a clean shutdown immediately after the EXIT transaction:
            # schedules exist in SQLite, but no process has collected them yet.
            connection = connect(path)
            try:
                persistence = TradeIntelligenceLogger.__new__(TradeIntelligenceLogger)
                persistence._persist_event(
                    connection,
                    lifecycle_event(trade_id, "NEW BUY", "Entry", exited_at),
                    {"symbol": "ANALYTICS_TEST"},
                    "",
                    None,
                )
                persistence._persist_event(
                    connection,
                    lifecycle_event(trade_id, "EXIT", "Exit", exited_at),
                    {"symbol": "ANALYTICS_TEST"},
                    "",
                    None,
                )
                connection.commit()
            finally:
                connection.close()

            recorder = TradeIntelligenceLogger(path)
            try:
                deadline = datetime.now() + timedelta(seconds=3)
                while datetime.now() < deadline:
                    connection = sqlite3.connect(path)
                    try:
                        completed = connection.execute(
                            "SELECT COUNT(*) FROM trade_post_exit_schedule "
                            "WHERE trade_id = ? AND completed_at IS NOT NULL",
                            (trade_id,),
                        ).fetchone()[0]
                    finally:
                        connection.close()
                    if completed == 5:
                        break
                    time.sleep(0.02)
                self.assertEqual(completed, 5)
            finally:
                recorder.close()

            connection = sqlite3.connect(path)
            try:
                snapshots = connection.execute(
                    "SELECT COUNT(*) FROM trade_post_exit_snapshots WHERE trade_id = ?",
                    (trade_id,),
                ).fetchone()[0]
            finally:
                connection.close()
            self.assertEqual(snapshots, 5)
        finally:
            self._remove_database(path)

    def test_migration_backfills_missing_legacy_post_exit_offsets(self):
        path = Path("data") / f"analytics-test-{uuid4().hex}.sqlite3"
        trade_id = f"T-ANALYTICS-MIGRATION-{uuid4().hex}"
        exited_at = (datetime.now() - timedelta(minutes=11)).isoformat(timespec="seconds")
        try:
            legacy = sqlite3.connect(path)
            try:
                legacy.executescript(SCHEMA)
                legacy.execute(
                    """
                    INSERT INTO trade_intelligence_trades (
                        trade_id, version, symbol, option_type, entered_at,
                        exited_at, entry_snapshot_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (trade_id, "test", "ANALYTICS_TEST", "CE", exited_at, exited_at, "{}"),
                )
                legacy.commit()
            finally:
                legacy.close()

            migrated = connect(path)
            try:
                scheduled = migrated.execute(
                    "SELECT COUNT(*) FROM trade_post_exit_schedule WHERE trade_id = ?",
                    (trade_id,),
                ).fetchone()[0]
                migration = migrated.execute(
                    "SELECT COUNT(*) FROM analytics_schema_migrations WHERE version = 2"
                ).fetchone()[0]
            finally:
                migrated.close()

            self.assertEqual(scheduled, 5)
            self.assertEqual(migration, 1)
        finally:
            self._remove_database(path)

    def test_trade_writer_retries_transient_sqlite_errors_and_reports_health(self):
        path = Path("data") / f"analytics-test-{uuid4().hex}.sqlite3"
        trade_id = f"T-ANALYTICS-RETRY-{uuid4().hex}"
        snapshot_manager.snapshots["ANALYTICS_TEST"] = MarketSnapshot(
            symbol="ANALYTICS_TEST", ltp=100.0
        )
        recorder = TradeIntelligenceLogger(path)
        original_persist = recorder._persist_event
        attempts = 0

        def fail_once(connection, *args):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise sqlite3.OperationalError("database is locked")
            return original_persist(connection, *args)

        try:
            recorder._persist_event = fail_once
            recorder(lifecycle_event(trade_id, "NEW BUY", "Entry"))
            recorder._queue.join()

            status = recorder.status()
            self.assertEqual(attempts, 2)
            self.assertGreaterEqual(status["retry_count"], 1)
            self.assertEqual(status["dropped_events"], 0)
            self.assertEqual(status["health"], "RUNNING")
        finally:
            self.assertTrue(recorder.close())
            self._remove_database(path)

    def test_queue_metrics_drop_counter_and_shutdown_flush_are_verified(self):
        path = Path("data") / f"analytics-test-{uuid4().hex}.sqlite3"
        recorder = TradeIntelligenceLogger(path, queue_size=1)
        started = Event()
        release = Event()
        original_persist = recorder._persist_event

        def block_first_write(connection, *args):
            started.set()
            self.assertTrue(release.wait(2))
            return original_persist(connection, *args)

        try:
            recorder._persist_event = block_first_write
            recorder(lifecycle_event(f"T-QUEUE-1-{uuid4().hex}", "NEW BUY", "Entry"))
            self.assertTrue(started.wait(2))
            recorder(lifecycle_event(f"T-QUEUE-2-{uuid4().hex}", "NEW BUY", "Entry"))
            recorder(lifecycle_event(f"T-QUEUE-3-{uuid4().hex}", "NEW BUY", "Entry"))

            status = recorder.status()
            self.assertEqual(status["queue_depth"], 1)
            self.assertEqual(status["max_queue_depth"], 1)
            self.assertEqual(status["dropped_events"], 1)

            release.set()
            self.assertTrue(recorder.close())
            status = recorder.status()
            self.assertTrue(status["shutdown_flush_verified"])
            self.assertEqual(status["pending_queue_tasks"], 0)
            self.assertEqual(status["health"], "STOPPED")
        finally:
            release.set()
            recorder.close()
            self._remove_database(path)

    def test_market_writer_retries_transient_sqlite_errors_and_reports_health(self):
        path = Path("data") / f"analytics-test-{uuid4().hex}.sqlite3"
        attempts = 0
        original_persist = MarketSessionRecorder._persist

        def fail_once(connection, snapshot):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise sqlite3.OperationalError("database is busy")
            return original_persist(connection, snapshot)

        try:
            with patch.object(MarketSessionRecorder, "_persist", side_effect=fail_once):
                recorder = MarketSessionRecorder(path, min_capture_interval_seconds=0)
                try:
                    recorder.observe({
                        "symbol": "NIFTY",
                        "exchange": "NSE_INDEX",
                        "mode": 2,
                        "data": {"open": 100.0, "ltp": 101.0},
                    })
                    recorder._queue.join()
                    status = recorder.status()
                    self.assertEqual(attempts, 2)
                    self.assertGreaterEqual(status["retry_count"], 1)
                    self.assertEqual(status["dropped_events"], 0)
                    self.assertEqual(status["health"], "RUNNING")
                finally:
                    self.assertTrue(recorder.close())
        finally:
            self._remove_database(path)

    def test_writer_recovers_after_initial_database_connection_failure(self):
        path = Path("data") / f"analytics-test-{uuid4().hex}.sqlite3"
        original_connect = connect
        attempts = 0

        def fail_first_connection(database_path):
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise sqlite3.OperationalError("database is locked")
            return original_connect(database_path)

        try:
            with patch("app.observability.trade_intelligence.connect", side_effect=fail_first_connection):
                recorder = TradeIntelligenceLogger(path)
                try:
                    deadline = time.monotonic() + 2
                    while recorder.status()["health"] == "RECONNECTING" and time.monotonic() < deadline:
                        time.sleep(0.02)
                    self.assertEqual(recorder.status()["health"], "DEGRADED")
                    self.assertGreaterEqual(recorder.status()["reconnect_count"], 1)
                finally:
                    self.assertTrue(recorder.close())
        finally:
            self._remove_database(path)

    def test_market_session_records_index_value_and_trend_without_scoring(self):
        path = Path("data") / f"analytics-test-{uuid4().hex}.sqlite3"
        try:
            recorder = MarketSessionRecorder(path, min_capture_interval_seconds=0)
            try:
                recorder.observe({
                    "symbol": "NIFTY",
                    "exchange": "NSE_INDEX",
                    "mode": 2,
                    "data": {
                        "timestamp": 123,
                        "open": 100.0,
                        "high": 105.0,
                        "low": 99.0,
                        "close": 100.0,
                        "ltp": 104.0,
                        "volume": 20,
                    },
                })
                recorder.observe({
                    "symbol": "NIFTY",
                    "exchange": "NSE_INDEX",
                    "mode": 3,
                    "data": {
                        "timestamp": 124,
                        "ltp": 104.0,
                        "depth": {
                            "buy": [{"price": 103.9, "quantity": 200}],
                            "sell": [{"price": 104.1, "quantity": 100}],
                        },
                    },
                })
                recorder._queue.join()
            finally:
                recorder.close()

            with sqlite3.connect(path) as connection:
                row = connection.execute(
                    "SELECT symbol, trend, score, confidence "
                    "FROM market_session_snapshots ORDER BY id DESC LIMIT 1"
                ).fetchone()
            connection.close()
            self.assertEqual(row[0], "NIFTY")
            self.assertEqual(row[1], "BULLISH")
            self.assertEqual(row[2:], (0, 0))
        finally:
            self._remove_database(path)

    def test_index_feed_is_not_added_to_the_stock_snapshot_store(self):
        class Capture:
            def __init__(self):
                self.quotes = []

            def observe(self, quote):
                self.quotes.append(quote)

        original = snapshot_manager.snapshots.pop("NIFTY", None)
        websocket = OpenAlgoWebSocket.__new__(OpenAlgoWebSocket)
        capture = Capture()
        websocket.market_session_recorder = capture
        quote = {
            "symbol": "NIFTY",
            "exchange": "NSE_INDEX",
            "mode": 2,
            "data": {"ltp": 100.0},
        }
        try:
            self.assertIsNone(websocket.on_quote(quote))
            self.assertEqual(capture.quotes, [quote])
            self.assertIsNone(snapshot_manager.get("NIFTY"))
        finally:
            if original is not None:
                snapshot_manager.snapshots["NIFTY"] = original

    @staticmethod
    def _remove_database(path):
        for candidate in (path, Path(f"{path}-wal"), Path(f"{path}-shm")):
            candidate.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
