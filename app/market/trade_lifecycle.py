"""In-memory trade lifecycle with hysteresis between scanner passes."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
from app.core.constants import APP_VERSION
from app.observability.lifecycle_events import (
    LifecycleTransitionEvent,
    SnapshotFingerprint,
)


@dataclass
class LifecycleTransition:
    timestamp: datetime
    from_state: str
    to_state: str
    reason: str


@dataclass
class TradeLifecycleRecord:
    symbol: str
    option_type: str | None = None
    state: str = "INVALID"
    entered_at: datetime | None = None
    updated_at: datetime | None = None
    confirmation_scans: int = 0
    weakening_scans: int = 0
    lifecycle_reason: str = "No valid trade setup"
    transitions: list[LifecycleTransition] = field(default_factory=list)
    trade_id: str | None = None
    trade_started_at: datetime | None = None
    confirmed_at: datetime | None = None


class TradeLifecycleEngine:
    """Owns live lifecycle state only; records are intentionally not durable."""

    CONFIRMATION_SCANS = 2
    EXIT_SCANS = 2
    ACTIVE_STATES = {"NEW BUY", "CONFIRMED", "HOLD", "WEAKENING"}

    def __init__(self, decision_engine, event_publisher=None):
        self.decision_engine = decision_engine
        self.event_publisher = event_publisher
        self.records: dict[str, TradeLifecycleRecord] = {}

    def analyze(self, snapshot, scan_id=0):
        record = self.records.setdefault(
            snapshot.symbol, TradeLifecycleRecord(symbol=snapshot.symbol)
        )
        now = datetime.now()

        if record.state in self.ACTIVE_STATES:
            self._evaluate_active_trade(record, snapshot, now, scan_id)
        else:
            self._evaluate_new_entry(record, snapshot, now, scan_id)

        self._apply_snapshot(record, snapshot)
        return snapshot

    def _evaluate_new_entry(self, record, snapshot, now, scan_id):
        entry = self.decision_engine.evaluate_entry(snapshot)
        if not entry.qualified:
            self._transition(record, snapshot, "INVALID", entry.reason, now, scan_id)
            return

        record.option_type = entry.option_type
        self._start_trade(record, now)
        record.confirmation_scans = 1
        record.weakening_scans = 0
        self._transition(record, snapshot, "NEW BUY", entry.reason, now, scan_id)

    def _evaluate_active_trade(self, record, snapshot, now, scan_id):
        exit_assessment = self.decision_engine.evaluate_exit(
            snapshot, record.option_type
        )

        if exit_assessment.hard_exit:
            record.weakening_scans = self.EXIT_SCANS
            next_state = "INVALID" if record.state == "NEW BUY" else "EXIT"
            self._transition(record, snapshot, next_state, exit_assessment.reason, now, scan_id)
            return

        if record.state == "NEW BUY":
            entry = self.decision_engine.evaluate_entry(snapshot)
            if entry.qualified and entry.option_type == record.option_type:
                record.confirmation_scans += 1
                record.weakening_scans = 0
                if record.confirmation_scans >= self.CONFIRMATION_SCANS:
                    record.confirmed_at = now
                    self._transition(
                        record,
                        snapshot,
                        "CONFIRMED",
                        f"Entry conditions held for {record.confirmation_scans} scans",
                        now,
                        scan_id,
                    )
                else:
                    self._transition(record, snapshot, "NEW BUY", entry.reason, now, scan_id)
            else:
                record.weakening_scans += 1
                if record.weakening_scans >= self.EXIT_SCANS:
                    self._transition(record, snapshot, "INVALID", entry.reason, now, scan_id)
                else:
                    self._transition(
                        record,
                        snapshot,
                        "NEW BUY",
                        f"Entry weakened; grace scan {record.weakening_scans} of {self.EXIT_SCANS}: {entry.reason}",
                        now,
                        scan_id,
                    )
            return

        if exit_assessment.soft_exit:
            record.weakening_scans += 1
            if record.weakening_scans >= self.EXIT_SCANS:
                self._transition(record, snapshot, "EXIT", exit_assessment.reason, now, scan_id)
            else:
                self._transition(
                    record,
                    snapshot,
                    "WEAKENING",
                    f"{exit_assessment.reason}; grace scan {record.weakening_scans} of {self.EXIT_SCANS}",
                    now,
                    scan_id,
                )
            return

        record.weakening_scans = 0
        self._transition(record, snapshot, "HOLD", exit_assessment.reason, now, scan_id)

    def _start_trade(self, record, now):
        date = now.strftime("%Y%m%d")
        # The readable prefix keeps existing analytics grouping conventions;
        # the UUID component prevents collisions after a process restart.
        record.trade_id = f"T-{record.symbol}-{date}-{uuid4().hex}"
        record.trade_started_at = now
        record.confirmed_at = None

    def _transition(self, record, snapshot, state, reason, now, scan_id):
        if record.state != state:
            transition = LifecycleTransition(now, record.state, state, reason)
            record.transitions.append(transition)
            previous_state = record.state
            record.state = state
            record.entered_at = now
            self._publish_transition(
                record, snapshot, previous_state, state, reason, now, scan_id
            )

        record.lifecycle_reason = reason
        record.updated_at = now

    def _publish_transition(
        self, record, snapshot, from_state, to_state, reason, timestamp, scan_id
    ):
        if not self.event_publisher or not record.trade_id:
            return
        fingerprint = SnapshotFingerprint(
            ltp=snapshot.ltp,
            score=snapshot.score,
            confidence=snapshot.confidence,
            trend=snapshot.trend,
            momentum=snapshot.momentum,
            rvol=snapshot.rvol,
            obi=snapshot.orderbook_imbalance,
            bid_pressure=snapshot.bid_pressure,
            ask_pressure=snapshot.ask_pressure,
            spread=snapshot.spread,
            lifecycle_reason=reason,
        )
        self.event_publisher.publish(
            LifecycleTransitionEvent(
                version=APP_VERSION,
                scan_id=scan_id,
                timestamp=timestamp,
                trade_id=record.trade_id,
                symbol=record.symbol,
                option_type=record.option_type or "NONE",
                from_state=from_state,
                to_state=to_state,
                lifecycle_reason=reason,
                trade_started_at=record.trade_started_at or timestamp,
                confirmed_at=record.confirmed_at,
                fingerprint=fingerprint,
            )
        )

    def _apply_snapshot(self, record, snapshot):
        actions = {
            "INVALID": "NO TRADE",
            "NEW BUY": f"BUY {record.option_type}",
            "CONFIRMED": f"BUY {record.option_type}",
            "HOLD": f"HOLD {record.option_type}",
            "WEAKENING": f"HOLD {record.option_type}",
            "EXIT": f"EXIT {record.option_type}",
        }
        snapshot.lifecycle_state = record.state
        snapshot.trade_id = record.trade_id or "-"
        snapshot.lifecycle_reason = record.lifecycle_reason
        snapshot.lifecycle_updated_at = (
            record.updated_at.isoformat(timespec="seconds")
            if record.updated_at else None
        )
        snapshot.action = actions[record.state]
        snapshot.signal_state = record.state
        snapshot.signal_age = int(
            (record.updated_at - record.entered_at).total_seconds()
        ) if record.updated_at and record.entered_at else 0
