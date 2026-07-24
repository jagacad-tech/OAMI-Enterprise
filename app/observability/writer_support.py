"""Shared reliability primitives for passive SQLite writers."""

import sqlite3
import threading
import time


MAX_SQLITE_RETRIES = 3
RETRY_BASE_SECONDS = 0.05


def is_transient_sqlite_error(error):
    """Return whether SQLite is likely to succeed after a short retry."""
    if not isinstance(error, sqlite3.Error):
        return False
    message = str(error).lower()
    return any(token in message for token in (
        "database is locked",
        "database is busy",
        "locked",
        "busy",
        "temporarily unavailable",
        "disk i/o error",
    ))


def retry_sqlite_operation(connection, operation, on_retry):
    """Run one transaction operation with bounded transient-error retries.

    ``operation`` must commit on success.  A failed attempt is rolled back
    before it is retried, so a caller never continues inside a partial write.
    """
    for attempt in range(MAX_SQLITE_RETRIES + 1):
        try:
            operation()
            return None
        except Exception as error:
            try:
                connection.rollback()
            except sqlite3.Error:
                pass
            if not is_transient_sqlite_error(error) or attempt == MAX_SQLITE_RETRIES:
                return error
            on_retry(error, attempt + 1)
            time.sleep(RETRY_BASE_SECONDS * (2 ** attempt))
    return RuntimeError("SQLite retry loop exited unexpectedly")


class WriterHealth:
    """Thread-safe health and delivery metrics exposed by passive writers."""

    def __init__(self, queue_capacity):
        self._lock = threading.Lock()
        self._queue_capacity = queue_capacity
        self._accepted_events = 0
        self._processed_events = 0
        self._dropped_events = 0
        self._retry_count = 0
        self._write_failures = 0
        self._reconnect_count = 0
        self._max_queue_depth = 0
        self._last_success_at = None
        self._last_error = None
        self._last_error_at = None
        self._connected = False
        self._shutdown_flush_verified = None

    def accepted(self, queue_depth):
        with self._lock:
            self._accepted_events += 1
            self._max_queue_depth = max(self._max_queue_depth, queue_depth)

    def dropped(self, error=None):
        with self._lock:
            self._dropped_events += 1
            if error is not None:
                self._set_error(error)

    def processed(self):
        with self._lock:
            self._processed_events += 1
            self._last_success_at = time.time()

    def retried(self, error, _attempt=None):
        with self._lock:
            self._retry_count += 1
            self._set_error(error)

    def failure(self, error):
        with self._lock:
            self._write_failures += 1
            self._set_error(error)

    def connected(self, reconnect=False):
        with self._lock:
            self._connected = True
            if reconnect:
                self._reconnect_count += 1

    def disconnected(self):
        with self._lock:
            self._connected = False

    def shutdown_flush(self, verified):
        with self._lock:
            self._shutdown_flush_verified = verified

    def status(self, queue, thread, closed):
        with self._lock:
            result = {
                "queue_depth": queue.qsize(),
                "queue_capacity": self._queue_capacity,
                "max_queue_depth": self._max_queue_depth,
                "accepted_events": self._accepted_events,
                "processed_events": self._processed_events,
                "dropped_events": self._dropped_events,
                "retry_count": self._retry_count,
                "write_failures": self._write_failures,
                "reconnect_count": self._reconnect_count,
                "last_success_at": self._last_success_at,
                "last_error": self._last_error,
                "last_error_at": self._last_error_at,
                "connected": self._connected,
                "shutdown_flush_verified": self._shutdown_flush_verified,
                "pending_queue_tasks": queue.unfinished_tasks,
                "worker_alive": thread.is_alive(),
            }

        if result["worker_alive"] and result["connected"]:
            result["health"] = "DEGRADED" if result["write_failures"] else "RUNNING"
        elif result["worker_alive"]:
            result["health"] = "RECONNECTING"
        elif closed and result["shutdown_flush_verified"]:
            result["health"] = "STOPPED"
        else:
            result["health"] = "UNHEALTHY"
        return result

    def _set_error(self, error):
        self._last_error = f"{type(error).__name__}: {error}"
        self._last_error_at = time.time()
