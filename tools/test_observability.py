"""Publish a synthetic lifecycle trade through OAMI observability.

Run from the repository root:
    python tools/test_observability.py

The command does not connect to OpenAlgo or require market data. It writes one
completed synthetic trade to ``data/observability_self_test.csv`` by default.
If Telegram is enabled and credentials are present, it dispatches three
clearly-labelled test notifications.
"""

import argparse
import csv
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from app.core.config import settings
from app.core.constants import APP_VERSION
from app.core.logger import logger
from app.observability.factory import build_lifecycle_event_bus
from app.observability.lifecycle_events import LifecycleTransitionEvent, SnapshotFingerprint
from app.observability.telegram_notifier import TelegramLifecycleNotifier


class _LifecycleLogCapture(logging.Handler):
    def __init__(self, trade_id):
        super().__init__()
        self.trade_id = trade_id
        self.seen = 0

    def emit(self, record):
        message = record.getMessage()
        if "LIFECYCLE" in message and self.trade_id in message:
            self.seen += 1


def _event(
    trade_id, started_at, timestamp, scan_id, from_state, to_state, reason,
    ltp, score, confidence, confirmed_at=None,
):
    return LifecycleTransitionEvent(
        version=APP_VERSION,
        scan_id=scan_id,
        timestamp=timestamp,
        trade_id=trade_id,
        symbol="OAMI-OBS-TEST",
        option_type="CE",
        from_state=from_state,
        to_state=to_state,
        lifecycle_reason=reason,
        trade_started_at=started_at,
        confirmed_at=confirmed_at,
        fingerprint=SnapshotFingerprint(
            ltp=ltp,
            score=score,
            confidence=confidence,
            trend="BULLISH",
            momentum="STRONG",
            rvol=2.5,
            obi=0.35,
            bid_pressure=240,
            ask_pressure=110,
            spread=0.05,
            lifecycle_reason=reason,
        ),
    )


def _csv_contains_trade(path, trade_id):
    if not path.exists():
        return False
    with path.open(newline="", encoding="utf-8") as source:
        return any(row.get("trade_id") == trade_id for row in csv.DictReader(source))


def main():
    parser = argparse.ArgumentParser(description="Run OAMI's offline observability self-test.")
    parser.add_argument(
        "--csv-path", type=Path, default=Path("data/observability_self_test.csv"),
        help="CSV output path for the synthetic completed trade.",
    )
    parser.add_argument(
        "--no-telegram", action="store_true",
        help="Do not dispatch the synthetic Telegram notifications.",
    )
    parser.add_argument(
        "--telegram-timeout", type=float, default=10,
        help="Seconds to wait for queued Telegram deliveries (default: 10).",
    )
    args = parser.parse_args()

    config = dict(settings.observability)
    config["csv_export_enabled"] = True
    config["completed_trades_path"] = str(args.csv_path)
    if args.no_telegram:
        config["telegram_enabled"] = False

    bus = build_lifecycle_event_bus(config)
    telegram_notifier = next(
        (item for item in bus._subscribers if isinstance(item, TelegramLifecycleNotifier)),
        None,
    )
    telegram_failure_count = (
        telegram_notifier.delivery_failure_count() if telegram_notifier else 0
    )
    trade_id = f"OBS-SELF-TEST-{uuid4().hex[:8].upper()}"
    started_at = datetime.now(timezone.utc).replace(microsecond=0)
    confirmed_at = started_at + timedelta(seconds=2)
    events = (
        _event(trade_id, started_at, started_at, 1, "INVALID", "NEW BUY", "Synthetic entry", 100.0, 80, 82),
        _event(trade_id, started_at, confirmed_at, 2, "NEW BUY", "CONFIRMED", "Synthetic confirmation", 101.5, 88, 91, confirmed_at),
        _event(trade_id, started_at, started_at + timedelta(seconds=4), 3, "CONFIRMED", "EXIT", "Synthetic test exit", 103.0, 76, 78, confirmed_at),
    )

    capture = _LifecycleLogCapture(trade_id)
    logger.addHandler(capture)
    try:
        for event in events:
            bus.publish(event)
    finally:
        logger.removeHandler(capture)

    checks = {
        "event bus": bus.event_count == len(events),
        "logging": capture.seen == len(events),
        "CSV export": _csv_contains_trade(args.csv_path, trade_id),
    }
    token_env = config.get("bot_token_env", "TELEGRAM_BOT_TOKEN")
    chat_id_env = config.get("chat_id_env", "TELEGRAM_CHAT_ID")
    print(
        "Telegram environment: "
        f"{token_env}={'loaded' if os.getenv(token_env) else 'missing'}, "
        f"{chat_id_env}={'loaded' if os.getenv(chat_id_env) else 'missing'}"
    )

    print(f"Synthetic trade: {trade_id}")
    for name, passed in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}: {name}")
    if telegram_notifier:
        telegram_delivered = telegram_notifier.wait_for_delivery(
            args.telegram_timeout, telegram_failure_count
        )
        print(
            "PASS: Telegram (three synthetic messages delivered)"
            if telegram_delivered
            else "FAIL: Telegram (delivery did not complete successfully)"
        )
    elif args.no_telegram:
        print("SKIPPED: Telegram (--no-telegram)")
    elif config.get("telegram_enabled", False):
        print("SKIPPED: Telegram (configured credentials are unavailable)")
    else:
        print("SKIPPED: Telegram (disabled in configuration)")

    return 0 if all(checks.values()) and (not telegram_notifier or telegram_delivered) else 1


if __name__ == "__main__":
    raise SystemExit(main())
