"""Asynchronous, read-only trade intelligence capture."""

import atexit
import json
from dataclasses import asdict
from datetime import datetime, timedelta
from queue import Empty, Full, Queue
import threading
import time

from app.core.logger import logger
from app.observability.analytics_database import connect
from app.observability.analytics_snapshot import snapshot_to_dict
from app.observability.writer_support import WriterHealth, retry_sqlite_operation
from app.services.snapshot_manager import snapshot_manager


POST_EXIT_OFFSETS_MINUTES = (1, 2, 3, 5, 10)
_STOP = object()


class TradeIntelligenceLogger:
    """Persist lifecycle facts without participating in trading decisions.

    The event-bus callback copies a snapshot and queues it. All SQLite work and
    delayed post-exit collection run in this daemon worker, outside the scanner.
    """

    def __init__(self, path, queue_size=1000, shutdown_timeout_seconds=15):
        self.path = path
        self._queue = Queue(maxsize=queue_size)
        self._stop = threading.Event()
        self._closed = False
        self._close_lock = threading.Lock()
        self._shutdown_timeout_seconds = shutdown_timeout_seconds
        self._health = WriterHealth(queue_size)
        self._thread = threading.Thread(
            target=self._run,
            name="trade-intelligence-writer",
            daemon=True,
        )
        self._thread.start()
        atexit.register(self.close)

    def __call__(self, event):
        """Copy the current analysis snapshot and enqueue the lifecycle event."""
        if self._closed:
            return
        underlying = self._capture_snapshot(event.symbol)
        option_symbol = (underlying or {}).get("option_symbol")
        option = self._capture_snapshot(option_symbol) if self._is_symbol(option_symbol) else None
        item = (event, underlying, option_symbol, option)
        # Serialize acceptance with close so no event can land after the stop
        # sentinel and be lost during a graceful shutdown.
        with self._close_lock:
            if self._closed:
                return
            try:
                self._queue.put_nowait(item)
                self._health.accepted(self._queue.qsize())
            except Full:
                self._health.dropped()
                logger.warning("Trade intelligence queue is full; dropping trade=%s", event.trade_id)

    def close(self):
        """Flush queued events during normal process shutdown."""
        with self._close_lock:
            if self._closed:
                return self.status()["shutdown_flush_verified"] is True
            self._closed = True
            self._stop.set()
            try:
                self._queue.put_nowait(_STOP)
            except Full:
                # The worker will drain the bounded queue and observe _stop.
                pass
        deadline = time.monotonic() + self._shutdown_timeout_seconds
        while self._queue.unfinished_tasks and time.monotonic() < deadline:
            time.sleep(0.01)
        remaining = max(0.0, deadline - time.monotonic())
        self._thread.join(timeout=remaining)
        verified = not self._queue.unfinished_tasks and not self._thread.is_alive()
        self._health.shutdown_flush(verified)
        if not verified:
            logger.error("Trade intelligence writer did not flush before shutdown")
        return verified

    def status(self):
        """Return queue, delivery, and worker-liveness metrics."""
        return self._health.status(self._queue, self._thread, self._closed)

    @staticmethod
    def _is_symbol(symbol):
        return bool(symbol and symbol != "-")

    @staticmethod
    def _capture_snapshot(symbol):
        if not symbol:
            return None
        with snapshot_manager.symbol_lock(symbol):
            return snapshot_to_dict(snapshot_manager.get(symbol))

    def _run(self):
        reconnecting = False
        while not self._stop.is_set() or not self._queue.empty():
            connection = None
            try:
                connection = connect(self.path)
                self._health.connected(reconnect=reconnecting)
                reconnecting = False
                while not self._stop.is_set() or not self._queue.empty():
                    collection_error = retry_sqlite_operation(
                        connection,
                        lambda: self._collect_and_commit_due_post_exit_snapshots(connection),
                        self._health.retried,
                    )
                    if collection_error is not None:
                        self._health.failure(collection_error)
                        logger.error(
                            "Trade intelligence post-exit collection failed: %s",
                            collection_error,
                        )
                    try:
                        item = self._queue.get(timeout=0.5)
                    except Empty:
                        continue
                    try:
                        if item is _STOP:
                            continue
                        error = retry_sqlite_operation(
                            connection,
                            lambda: self._persist_and_commit(connection, *item),
                            self._health.retried,
                        )
                        if error is None:
                            self._health.processed()
                        else:
                            self._health.failure(error)
                            self._health.dropped(error)
                            logger.error(
                                "Trade intelligence persistence failed: %s",
                                error,
                            )
                    finally:
                        self._queue.task_done()
            except Exception as error:
                self._health.failure(error)
                self._health.disconnected()
                reconnecting = True
                logger.exception("Trade intelligence writer connection failed")
                if not self._stop.is_set() or not self._queue.empty():
                    time.sleep(0.1)
            finally:
                if connection is not None:
                    try:
                        connection.close()
                    except Exception as error:
                        self._health.failure(error)
                        logger.exception("Trade intelligence writer connection close failed")
                self._health.disconnected()
        self._health.disconnected()

    def _persist_and_commit(self, connection, event, underlying, option_symbol, option):
        self._persist_event(connection, event, underlying, option_symbol, option)
        connection.commit()

    def _collect_and_commit_due_post_exit_snapshots(self, connection):
        self._collect_due_post_exit_snapshots(connection)

    def _persist_event(self, connection, event, underlying, option_symbol, option):
        event_time = event.timestamp.isoformat(timespec="seconds")
        snapshot_json = self._json(underlying)
        fingerprint_json = self._json(asdict(event.fingerprint))

        connection.execute(
            """
            INSERT INTO trade_lifecycle_transitions (
                trade_id, transition_at, scan_id, from_state, to_state,
                lifecycle_reason, snapshot_json, fingerprint_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.trade_id,
                event_time,
                event.scan_id,
                event.from_state,
                event.to_state,
                event.lifecycle_reason,
                snapshot_json,
                fingerprint_json,
            ),
        )

        if event.to_state == "NEW BUY":
            connection.execute(
                """
                INSERT OR IGNORE INTO trade_intelligence_trades (
                    trade_id, version, symbol, option_type, entered_at,
                    confirmed_at, entry_snapshot_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.trade_id,
                    event.version,
                    event.symbol,
                    event.option_type,
                    event.trade_started_at.isoformat(timespec="seconds"),
                    self._timestamp(event.confirmed_at),
                    snapshot_json,
                ),
            )

        if event.to_state == "CONFIRMED":
            connection.execute(
                "UPDATE trade_intelligence_trades SET confirmed_at = ? WHERE trade_id = ?",
                (self._timestamp(event.confirmed_at), event.trade_id),
            )

        if event.to_state == "EXIT":
            connection.execute(
                """
                UPDATE trade_intelligence_trades
                SET exited_at = ?, exit_reason = ?, exit_snapshot_json = ?
                WHERE trade_id = ?
                """,
                (event_time, event.lifecycle_reason, snapshot_json, event.trade_id),
            )
            self._schedule_post_exit_snapshots(
                connection, event, option_symbol or ""
            )

    @staticmethod
    def _schedule_post_exit_snapshots(connection, event, option_symbol):
        """Persist all due times atomically with the EXIT analytics event."""
        created_at = datetime.now().isoformat(timespec="seconds")
        for offset in POST_EXIT_OFFSETS_MINUTES:
            scheduled_at = event.timestamp + timedelta(minutes=offset)
            connection.execute(
                """
                INSERT OR IGNORE INTO trade_post_exit_schedule (
                    trade_id, offset_minutes, symbol, option_symbol,
                    scheduled_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event.trade_id,
                    offset,
                    event.symbol,
                    option_symbol,
                    scheduled_at.isoformat(timespec="seconds"),
                    created_at,
                ),
            )

    def _collect_due_post_exit_snapshots(self, connection):
        """Capture every due durable schedule, including work from a restart."""
        now = datetime.now().isoformat(timespec="seconds")
        ready = connection.execute(
            """
            SELECT trade_id, symbol, option_symbol, offset_minutes, scheduled_at
            FROM trade_post_exit_schedule
            WHERE completed_at IS NULL AND scheduled_at <= ?
            ORDER BY scheduled_at, trade_id, offset_minutes
            """,
            (now,),
        ).fetchall()
        for trade_id, symbol, option_symbol, offset, scheduled_at in ready:
            underlying = self._capture_snapshot(symbol)
            option = self._capture_snapshot(option_symbol) if self._is_symbol(option_symbol) else None
            status = "AVAILABLE" if option is not None else "NOT_SUBSCRIBED_OR_UNAVAILABLE"
            connection.execute(
                """
                INSERT OR IGNORE INTO trade_post_exit_snapshots (
                    trade_id, offset_minutes, scheduled_at, captured_at,
                    underlying_snapshot_json, option_symbol, option_snapshot_json,
                    option_snapshot_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trade_id,
                    offset,
                    scheduled_at,
                    datetime.now().isoformat(timespec="seconds"),
                    self._json(underlying),
                    option_symbol or "",
                    self._json(option),
                    status,
                ),
            )
            connection.execute(
                """
                UPDATE trade_post_exit_schedule
                SET completed_at = ?
                WHERE trade_id = ? AND offset_minutes = ? AND completed_at IS NULL
                """,
                (datetime.now().isoformat(timespec="seconds"), trade_id, offset),
            )
        if ready:
            connection.commit()

    @staticmethod
    def _timestamp(value):
        return value.isoformat(timespec="seconds") if value else None

    @staticmethod
    def _json(value):
        return json.dumps(value, separators=(",", ":"), sort_keys=True)
