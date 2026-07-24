"""Reliable execution and monitoring for the market scanner.

This module owns no trading, scoring, lifecycle, or strategy logic.  It only
serializes scanner execution and provides fault containment and liveness
monitoring around the existing ``Scanner`` implementation.
"""

from datetime import datetime, timezone
import threading
import time

from app.core.logger import logger


class ScannerService:
    """Run exactly one scanner worker with heartbeat and watchdog supervision."""

    _active_service_lock = threading.Lock()
    _active_service = None

    def __init__(
        self,
        scanner,
        on_scan_completed=None,
        scan_interval_seconds=5,
        heartbeat_interval_seconds=30,
        watchdog_timeout_seconds=60,
        monitor_interval_seconds=1,
        restart_backoff_max_seconds=30,
    ):
        self.scanner = scanner
        self.on_scan_completed = on_scan_completed
        self.scan_interval_seconds = scan_interval_seconds
        self.heartbeat_interval_seconds = heartbeat_interval_seconds
        self.watchdog_timeout_seconds = watchdog_timeout_seconds
        self.monitor_interval_seconds = monitor_interval_seconds
        self.restart_backoff_max_seconds = restart_backoff_max_seconds

        # Lifecycle serialization prevents simultaneous start/stop/restart
        # operations. State protects values shared by worker and monitor.
        self._lifecycle_lock = threading.RLock()
        self._state_lock = threading.Lock()
        self._restart_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._restart_requested = threading.Event()
        self._scanner_thread = None
        self._monitor_thread = None
        self._shutdown_in_progress = False
        self._generation = 0

        self._completed_scan_count = 0
        self._last_completed_at = None
        self._last_completed_monotonic = None
        self._last_scan_duration_seconds = None
        self._scan_in_progress = False
        self._current_scan_started_monotonic = None
        self._next_scan_due_monotonic = None
        self._started_monotonic = None
        self._last_heartbeat_monotonic = None
        self._last_watchdog_action_monotonic = None
        self._consecutive_restart_count = 0
        self._next_restart_monotonic = None

    def start(self):
        """Start one worker and one monitor; concurrent calls are idempotent."""
        with self._lifecycle_lock:
            with self._state_lock:
                if self._shutdown_in_progress or (
                    self._monitor_thread and self._monitor_thread.is_alive()
                ) or (
                    self._scanner_thread and self._scanner_thread.is_alive()
                ):
                    return False
            if not self._claim_process_scanner():
                logger.error("Scanner service start rejected: another scanner service is active")
                return False

            with self._state_lock:
                self._stop_event.clear()
                self._restart_requested.clear()
                self._completed_scan_count = 0
                self._last_completed_at = None
                self._last_completed_monotonic = None
                self._last_scan_duration_seconds = None
                self._scan_in_progress = False
                self._current_scan_started_monotonic = None
                self._next_scan_due_monotonic = None
                self._started_monotonic = time.monotonic()
                self._last_heartbeat_monotonic = self._started_monotonic
                self._last_watchdog_action_monotonic = None
                self._consecutive_restart_count = 0
                self._next_restart_monotonic = None

            if not self._start_scanner_worker("service start"):
                logger.error("Scanner service failed to start its worker")
                self._release_process_scanner()
                return False

            monitor = threading.Thread(
                target=self._monitor_loop,
                name="oami-scanner-monitor",
                daemon=True,
            )
            with self._state_lock:
                self._monitor_thread = monitor
            monitor.start()

        logger.info("Scanner service started")
        return True

    def stop(self, join_timeout_seconds=10):
        """Stop monitoring and request the sole worker to exit cooperatively."""
        with self._lifecycle_lock:
            with self._state_lock:
                if self._shutdown_in_progress:
                    return
                self._shutdown_in_progress = True
            self._stop_event.set()
            self._restart_requested.set()

            with self._state_lock:
                scanner_thread = self._scanner_thread
                monitor_thread = self._monitor_thread

        # Do not hold the lifecycle lock while joining: the monitor may be
        # completing a watchdog restart attempt and needs that lock to observe
        # the stop event and exit.
        if scanner_thread and scanner_thread is not threading.current_thread():
            scanner_thread.join(join_timeout_seconds)
        if monitor_thread and monitor_thread is not threading.current_thread():
            monitor_thread.join(join_timeout_seconds)

        scanner_alive = bool(scanner_thread and scanner_thread.is_alive())
        monitor_alive = bool(monitor_thread and monitor_thread.is_alive())
        if scanner_alive:
            logger.error(
                "Scanner worker did not stop within %s seconds",
                join_timeout_seconds,
            )
        if monitor_alive:
            logger.error(
                "Scanner monitor did not stop within %s seconds",
                join_timeout_seconds,
            )
        with self._lifecycle_lock:
            with self._state_lock:
                self._shutdown_in_progress = False
            if not scanner_alive and not monitor_alive:
                self._release_process_scanner()
            else:
                logger.error(
                    "Scanner service retained process ownership because a thread is still alive"
                )

        logger.info("Scanner service stopped")

    def _claim_process_scanner(self):
        """Claim the process-wide scanner slot before creating any worker."""
        with self._active_service_lock:
            active = self._active_service
            if active is not None and active is not self:
                active_status = active.status()
                if (
                    active_status["scanner_thread_alive"]
                    or active_status["monitor_thread_alive"]
                ):
                    return False
            self.__class__._active_service = self
            return True

    def _release_process_scanner(self):
        with self._active_service_lock:
            if self._active_service is self:
                self.__class__._active_service = None

    def status(self):
        """Return a thread-safe liveness snapshot for heartbeat and diagnostics."""
        with self._state_lock:
            scanner_thread = self._scanner_thread
            monitor_thread = self._monitor_thread
            last_completed_at = self._last_completed_at
            completed_scan_count = self._completed_scan_count
            last_scan_duration_seconds = self._last_scan_duration_seconds
            scan_in_progress = self._scan_in_progress

        scanner_alive = bool(scanner_thread and scanner_thread.is_alive())
        monitor_alive = bool(monitor_thread and monitor_thread.is_alive())
        if self._stop_event.is_set():
            state = "STOPPING"
        elif not scanner_alive:
            state = "UNHEALTHY"
        elif scan_in_progress:
            state = "SCANNING"
        else:
            state = "RUNNING"

        return {
            "status": state,
            "scan_count": completed_scan_count,
            "last_completed_scan_time": (
                last_completed_at.isoformat() if last_completed_at else None
            ),
            "last_scan_duration_seconds": last_scan_duration_seconds,
            "scan_in_progress": scan_in_progress,
            "scanner_thread_alive": scanner_alive,
            "monitor_thread_alive": monitor_alive,
        }

    def _start_scanner_worker(self, reason):
        """Start a replacement only after the previous worker has ended."""
        with self._lifecycle_lock:
            with self._restart_lock:
                with self._state_lock:
                    current = self._scanner_thread
                    if self._stop_event.is_set() or (current and current.is_alive()):
                        return False
                    self._generation += 1
                    generation = self._generation
                    self._restart_requested.clear()
                    worker = threading.Thread(
                        target=self._scanner_loop,
                        args=(generation,),
                        name=f"oami-scanner-{generation}",
                        daemon=True,
                    )
                    self._scanner_thread = worker

                worker.start()

        logger.info(
            "Scanner worker started: generation=%s reason=%s", generation, reason
        )
        return True

    def _scanner_loop(self, generation):
        """Top-level exception containment for the scanner worker."""
        try:
            while not self._stop_event.is_set() and not self._restart_requested.is_set():
                results = None
                scan_completed = False
                self._begin_scan()
                try:
                    results = self.scanner.scan()
                    self._record_completed_scan()
                    scan_completed = True
                except Exception:
                    # Scanner.scan has its own containment as well. Retaining
                    # this boundary protects the worker from future changes.
                    logger.exception("Scanner worker pass failed: generation=%s", generation)
                finally:
                    self._finish_scan()

                if scan_completed:
                    self._notify_scan_completed(results, generation)
                self._wait_for_next_pass()
        except BaseException:
            # Preserve a full trace for unexpected SystemExit-style failures;
            # the watchdog can replace a worker only after it has exited.
            logger.exception("Scanner worker stopped unexpectedly: generation=%s", generation)
        finally:
            with self._state_lock:
                if generation == self._generation:
                    self._scanner_thread = None
                    self._scan_in_progress = False
                    self._current_scan_started_monotonic = None
            logger.info("Scanner worker exited: generation=%s", generation)

    def _begin_scan(self):
        with self._state_lock:
            self._scan_in_progress = True
            self._current_scan_started_monotonic = time.monotonic()
            self._next_scan_due_monotonic = None

    def _finish_scan(self):
        finished_at = time.monotonic()
        with self._state_lock:
            started_at = self._current_scan_started_monotonic
            self._scan_in_progress = False
            self._current_scan_started_monotonic = None
            if started_at is not None:
                self._last_scan_duration_seconds = round(finished_at - started_at, 4)

    def _record_completed_scan(self):
        completed_at = datetime.now(timezone.utc)
        with self._state_lock:
            self._completed_scan_count += 1
            self._last_completed_at = completed_at
            self._last_completed_monotonic = time.monotonic()
            self._last_watchdog_action_monotonic = None
            self._consecutive_restart_count = 0
            self._next_restart_monotonic = None

    def _notify_scan_completed(self, results, generation):
        if self.on_scan_completed is None:
            return
        try:
            self.on_scan_completed(results)
        except Exception:
            logger.exception(
                "Scanner completion handler failed: generation=%s", generation
            )

    def _wait_for_next_pass(self):
        deadline = time.monotonic() + self.scan_interval_seconds
        with self._state_lock:
            self._next_scan_due_monotonic = deadline
        while not self._stop_event.is_set() and not self._restart_requested.is_set():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return
            self._stop_event.wait(min(remaining, 0.5))

    def _monitor_loop(self):
        """Emit liveness telemetry and supervise the scanner worker."""
        try:
            while not self._stop_event.wait(self.monitor_interval_seconds):
                try:
                    now = time.monotonic()
                    with self._state_lock:
                        heartbeat_due = (
                            now - self._last_heartbeat_monotonic
                            >= self.heartbeat_interval_seconds
                        )
                    if heartbeat_due:
                        self._log_heartbeat()
                        with self._state_lock:
                            self._last_heartbeat_monotonic = now
                    self._run_watchdog(now)
                except Exception:
                    # A telemetry or restart failure must not disable the
                    # monitor that protects the scanner worker.
                    logger.exception("Scanner monitor iteration failed")
        except BaseException:
            logger.exception("Scanner monitor stopped unexpectedly")

    def _log_heartbeat(self):
        status = self.status()
        duration = status["last_scan_duration_seconds"]
        logger.info(
            "Scanner heartbeat: status=%s scan_count=%s "
            "last_completed_scan_time=%s last_scan_duration_seconds=%s "
            "scan_in_progress=%s scanner_thread_alive=%s monitor_thread_alive=%s",
            status["status"],
            status["scan_count"],
            status["last_completed_scan_time"] or "never",
            duration if duration is not None else "never",
            status["scan_in_progress"],
            status["scanner_thread_alive"],
            status["monitor_thread_alive"],
        )

    def _run_watchdog(self, now):
        """Restart only dead or non-scanning stale workers.

        Python cannot safely terminate a live thread. A scan that is still in
        progress is therefore reported as stalled but is never replaced until
        it has returned, preserving the single-scanner guarantee.
        """
        with self._state_lock:
            last_completion = self._last_completed_monotonic or self._started_monotonic
            scanner_thread = self._scanner_thread
            scan_in_progress = self._scan_in_progress
            next_scan_due = self._next_scan_due_monotonic
            next_restart = self._next_restart_monotonic
            last_action = self._last_watchdog_action_monotonic

            if last_completion is None or now - last_completion < self.watchdog_timeout_seconds:
                return

            scanner_alive = bool(scanner_thread and scanner_thread.is_alive())
            if scanner_alive and scan_in_progress:
                if last_action is None:
                    self._last_watchdog_action_monotonic = now
                    logger.error(
                        "Scanner watchdog detected a scan running longer than %s seconds; "
                        "replacement deferred until the active scan exits",
                        self.watchdog_timeout_seconds,
                    )
                return

            if scanner_alive:
                if next_scan_due is not None and now < next_scan_due:
                    # The worker is intentionally waiting for its configured
                    # cadence, so lack of a new completion is not a stall.
                    return
                if last_action is not None and now - last_action < self.watchdog_timeout_seconds:
                    return
                self._last_watchdog_action_monotonic = now
                # The worker is between scans or in its completion handler.
                # It will exit before a replacement can be created.
                self._restart_requested.set()
                logger.error(
                    "Scanner watchdog detected no completed scan for %s seconds; "
                    "requesting restart after non-scanning stall",
                    self.watchdog_timeout_seconds,
                )
                return

            if next_restart is not None and now < next_restart:
                return
            self._consecutive_restart_count += 1
            restart_attempt = self._consecutive_restart_count
            delay = min(
                2 ** (restart_attempt - 1),
                self.restart_backoff_max_seconds,
            )
            self._next_restart_monotonic = now + delay

        logger.error(
            "Scanner watchdog restarting dead worker after %s seconds without a completed "
            "scan: attempt=%s next_backoff_seconds=%s",
            self.watchdog_timeout_seconds,
            restart_attempt,
            delay,
        )
        self._start_scanner_worker("watchdog stale worker")
