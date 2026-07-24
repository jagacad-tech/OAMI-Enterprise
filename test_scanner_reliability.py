"""Regression coverage for scanner fault containment and liveness monitoring."""

import threading
import time
import unittest

from app.market.models import MarketSnapshot
from app.market.scanner import Scanner
from app.market.scanner_service import ScannerService
from app.services.snapshot_manager import snapshot_manager


class ScannerReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.original_snapshots = snapshot_manager.snapshots
        snapshot_manager.snapshots = {}

    def tearDown(self):
        snapshot_manager.snapshots = self.original_snapshots

    def test_failed_symbol_does_not_prevent_later_symbols(self):
        scanner = Scanner()
        snapshot_manager.snapshots = {
            "BROKEN": MarketSnapshot(symbol="BROKEN"),
            "HEALTHY": MarketSnapshot(symbol="HEALTHY"),
        }
        processed = []
        original_analyze = scanner.depth_engine.analyze

        def analyze(snapshot):
            processed.append(snapshot.symbol)
            if snapshot.symbol == "BROKEN":
                raise RuntimeError("synthetic symbol failure")
            return original_analyze(snapshot)

        scanner.depth_engine.analyze = analyze
        results = scanner.scan()

        self.assertEqual(processed, ["BROKEN", "HEALTHY"])
        self.assertEqual([snapshot.symbol for snapshot in results], ["HEALTHY"])

    def test_index_snapshot_is_never_sent_to_the_scanner_pipeline(self):
        scanner = Scanner()
        snapshot_manager.snapshots = {
            "NIFTY": MarketSnapshot(symbol="NIFTY", ltp=100.0),
            "HEALTHY": MarketSnapshot(symbol="HEALTHY", ltp=100.0),
        }
        processed = []

        def capture(symbol, snapshot):
            processed.append(symbol)
            return snapshot

        scanner._scan_symbol = capture
        results = scanner.scan()

        self.assertEqual(processed, ["HEALTHY"])
        self.assertEqual([snapshot.symbol for snapshot in results], ["HEALTHY"])

    def test_worker_recovers_after_unexpected_exit(self):
        class ExitsOnceScanner:
            def __init__(self):
                self.calls = 0
                self.completed = threading.Event()

            def scan(self):
                self.calls += 1
                if self.calls == 1:
                    raise SystemExit("synthetic worker exit")
                self.completed.set()
                return []

        scanner = ExitsOnceScanner()
        service = ScannerService(
            scanner,
            scan_interval_seconds=0.01,
            heartbeat_interval_seconds=0.02,
            watchdog_timeout_seconds=0.05,
            monitor_interval_seconds=0.01,
        )
        service.start()
        try:
            self.assertTrue(scanner.completed.wait(1), "watchdog did not restart worker")
            status = service.status()
            self.assertGreaterEqual(status["scan_count"], 1)
            self.assertTrue(status["scanner_thread_alive"])
        finally:
            service.stop(join_timeout_seconds=1)

    def test_heartbeat_status_contains_required_liveness_fields(self):
        class HealthyScanner:
            def scan(self):
                return []

        service = ScannerService(HealthyScanner(), scan_interval_seconds=0.01)
        service.start()
        try:
            deadline = time.monotonic() + 1
            while service.status()["scan_count"] == 0 and time.monotonic() < deadline:
                time.sleep(0.01)
            status = service.status()
            self.assertIn("scan_count", status)
            self.assertIn("last_completed_scan_time", status)
            self.assertIn("last_scan_duration_seconds", status)
            self.assertIn("scanner_thread_alive", status)
        finally:
            service.stop(join_timeout_seconds=1)

    def test_concurrent_start_creates_only_one_scanner_worker(self):
        class BlockingScanner:
            def __init__(self):
                self.started = threading.Event()
                self.release = threading.Event()
                self.calls = 0

            def scan(self):
                self.calls += 1
                self.started.set()
                self.release.wait(1)
                return []

        scanner = BlockingScanner()
        service = ScannerService(scanner, scan_interval_seconds=1)
        barrier = threading.Barrier(3)
        results = []

        def start_service():
            barrier.wait()
            results.append(service.start())

        first = threading.Thread(target=start_service)
        second = threading.Thread(target=start_service)
        first.start()
        second.start()
        barrier.wait()
        first.join(1)
        second.join(1)
        try:
            self.assertEqual(sorted(results), [False, True])
            self.assertTrue(scanner.started.wait(1))
            self.assertEqual(scanner.calls, 1)
            self.assertEqual(service._generation, 1)
        finally:
            scanner.release.set()
            service.stop(join_timeout_seconds=1)

    def test_watchdog_never_restarts_an_active_scan(self):
        class BlockingScanner:
            def __init__(self):
                self.started = threading.Event()
                self.release = threading.Event()
                self.completed = threading.Event()
                self.calls = 0

            def scan(self):
                self.calls += 1
                self.started.set()
                self.release.wait(1)
                self.completed.set()
                return []

        scanner = BlockingScanner()
        service = ScannerService(
            scanner,
            scan_interval_seconds=1,
            watchdog_timeout_seconds=0.05,
            monitor_interval_seconds=0.01,
        )
        service.start()
        try:
            self.assertTrue(scanner.started.wait(1))
            time.sleep(0.12)
            self.assertEqual(scanner.calls, 1)
            self.assertEqual(service._generation, 1)
            self.assertTrue(service.status()["scan_in_progress"])

            scanner.release.set()
            self.assertTrue(scanner.completed.wait(1))
            time.sleep(0.02)
            self.assertEqual(service._generation, 1)
        finally:
            scanner.release.set()
            service.stop(join_timeout_seconds=1)

    def test_second_service_cannot_create_a_duplicate_scanner(self):
        class BlockingScanner:
            def __init__(self):
                self.started = threading.Event()
                self.release = threading.Event()

            def scan(self):
                self.started.set()
                self.release.wait(1)
                return []

        scanner = BlockingScanner()
        first = ScannerService(scanner, scan_interval_seconds=1)
        second = ScannerService(scanner, scan_interval_seconds=1)
        self.assertTrue(first.start())
        try:
            self.assertTrue(scanner.started.wait(1))
            self.assertFalse(second.start())
            self.assertEqual(first._generation, 1)
            self.assertEqual(second._generation, 0)
        finally:
            scanner.release.set()
            first.stop(join_timeout_seconds=1)


if __name__ == "__main__":
    unittest.main()
