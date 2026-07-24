"""Passive index market-session analytics recorder."""

import atexit
import json
from datetime import datetime
from queue import Empty, Full, Queue
import threading
import time

from app.core.logger import logger
from app.market.indexes import INDEX_EXCHANGES, INDEX_SYMBOLS
from app.market.models import MarketSnapshot
from app.observability.analytics_database import connect
from app.observability.analytics_snapshot import snapshot_to_dict
from app.observability.writer_support import WriterHealth, retry_sqlite_operation


_STOP = object()


class MarketSessionRecorder:
    """Persist display-only index snapshots without trading-pipeline use."""

    def __init__(
        self, path, min_capture_interval_seconds=1.0, queue_size=5000,
        shutdown_timeout_seconds=15,
    ):
        self.path = path
        self.min_capture_interval_seconds = min_capture_interval_seconds
        self._queue = Queue(maxsize=queue_size)
        self._stop = threading.Event()
        self._closed = False
        self._close_lock = threading.Lock()
        self._shutdown_timeout_seconds = shutdown_timeout_seconds
        self._health = WriterHealth(queue_size)
        self._snapshots = {}
        self._last_capture = {}
        self._thread = threading.Thread(
            target=self._run,
            name="market-session-writer",
            daemon=True,
        )
        self._thread.start()
        atexit.register(self.close)

    @classmethod
    def accepts(cls, quote):
        return (
            quote.get("symbol") in INDEX_SYMBOLS
            and quote.get("exchange") in INDEX_EXCHANGES
        )

    def observe(self, quote):
        """Queue a raw index feed update; no market data processing is synchronous."""
        if self._closed:
            return
        with self._close_lock:
            if self._closed:
                return self.status()["shutdown_flush_verified"] is True
            try:
                self._queue.put_nowait(quote)
                self._health.accepted(self._queue.qsize())
            except Full:
                self._health.dropped()
                logger.warning("Market session queue is full; dropping index=%s", quote.get("symbol"))

    def close(self):
        with self._close_lock:
            if self._closed:
                return
            self._closed = True
            self._stop.set()
            try:
                self._queue.put_nowait(_STOP)
            except Full:
                # A full queue is still drained asynchronously before exit.
                pass
        deadline = time.monotonic() + self._shutdown_timeout_seconds
        while self._queue.unfinished_tasks and time.monotonic() < deadline:
            time.sleep(0.01)
        remaining = max(0.0, deadline - time.monotonic())
        self._thread.join(timeout=remaining)
        verified = not self._queue.unfinished_tasks and not self._thread.is_alive()
        self._health.shutdown_flush(verified)
        if not verified:
            logger.error("Market session writer did not flush before shutdown")
        return verified

    def status(self):
        """Return queue, delivery, and worker-liveness metrics."""
        return self._health.status(self._queue, self._thread, self._closed)

    def _run(self):
        reconnecting = False
        while not self._stop.is_set() or not self._queue.empty():
            connection = None
            try:
                connection = connect(self.path)
                self._health.connected(reconnect=reconnecting)
                reconnecting = False
                while not self._stop.is_set() or not self._queue.empty():
                    try:
                        quote = self._queue.get(timeout=0.5)
                    except Empty:
                        continue
                    try:
                        if quote is _STOP:
                            continue
                        snapshot = self._apply(quote)
                        if self._should_capture(snapshot):
                            error = retry_sqlite_operation(
                                connection,
                                lambda: self._persist_and_commit(connection, snapshot),
                                self._health.retried,
                            )
                            if error is None:
                                self._health.processed()
                            else:
                                self._health.failure(error)
                                self._health.dropped(error)
                                logger.error(
                                    "Market session analytics persistence failed: %s",
                                    error,
                                )
                        else:
                            self._health.processed()
                    except Exception as error:
                        self._health.failure(error)
                        self._health.dropped(error)
                        logger.exception("Market session analytics event failed")
                    finally:
                        self._queue.task_done()
            except Exception as error:
                self._health.failure(error)
                self._health.disconnected()
                reconnecting = True
                logger.exception("Market session writer connection failed")
                if not self._stop.is_set() or not self._queue.empty():
                    time.sleep(0.1)
            finally:
                if connection is not None:
                    try:
                        connection.close()
                    except Exception as error:
                        self._health.failure(error)
                        logger.exception("Market session writer connection close failed")
                self._health.disconnected()
        self._health.disconnected()

    @staticmethod
    def _persist_and_commit(connection, snapshot):
        MarketSessionRecorder._persist(connection, snapshot)
        connection.commit()

    def _apply(self, quote):
        symbol = quote["symbol"]
        data = quote.get("data", {})
        snapshot = self._snapshots.setdefault(
            symbol,
            MarketSnapshot(symbol=symbol, exchange=quote.get("exchange", "NSE_INDEX"), instrument_type="INDEX"),
        )
        mode = quote.get("mode")
        timestamp = data.get("timestamp", snapshot.timestamp)
        snapshot.timestamp = timestamp
        if mode == 2:
            snapshot.quote_updated_at = timestamp
            for field in ("open", "high", "low", "close", "ltp", "volume"):
                setattr(snapshot, field, data.get(field, getattr(snapshot, field)))
        elif mode == 3:
            snapshot.depth_updated_at = timestamp
            snapshot.ltp = data.get("ltp", snapshot.ltp)
            snapshot.depth = data.get("depth", snapshot.depth)

        self._derive_trend(snapshot)
        return snapshot

    def _should_capture(self, snapshot):
        now = datetime.now().timestamp()
        previous = self._last_capture.get(snapshot.symbol, 0.0)
        if now - previous < self.min_capture_interval_seconds:
            return False
        self._last_capture[snapshot.symbol] = now
        return True

    @staticmethod
    def _derive_trend(snapshot):
        """Derive the sole dashboard indicator from the current session open."""
        try:
            open_price = float(snapshot.open)
            latest_price = float(snapshot.ltp)
        except (TypeError, ValueError):
            snapshot.trend = "NEUTRAL"
            return

        if open_price <= 0 or latest_price == open_price:
            snapshot.trend = "NEUTRAL"
        elif latest_price > open_price:
            snapshot.trend = "BULLISH"
        else:
            snapshot.trend = "BEARISH"

    @staticmethod
    def _persist(connection, snapshot):
        captured_at = datetime.now().isoformat(timespec="seconds")
        connection.execute(
            """
            INSERT INTO market_session_snapshots (
                captured_at, market_timestamp, symbol, exchange, ltp, trend,
                momentum, rvol, bid_pressure, ask_pressure, orderbook_imbalance,
                spread, score, confidence, snapshot_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                captured_at,
                str(snapshot.timestamp) if snapshot.timestamp is not None else None,
                snapshot.symbol,
                snapshot.exchange,
                snapshot.ltp,
                snapshot.trend,
                snapshot.momentum,
                snapshot.rvol,
                snapshot.bid_pressure,
                snapshot.ask_pressure,
                snapshot.orderbook_imbalance,
                snapshot.spread,
                snapshot.score,
                snapshot.confidence,
                json.dumps(snapshot_to_dict(snapshot), separators=(",", ":"), sort_keys=True),
            ),
        )
