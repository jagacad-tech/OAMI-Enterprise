"""Immutable event contracts for lifecycle observability."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class SnapshotFingerprint:
    ltp: float
    score: int
    confidence: int
    trend: str
    momentum: str
    rvol: float
    obi: float
    bid_pressure: int
    ask_pressure: int
    spread: float
    lifecycle_reason: str


@dataclass(frozen=True)
class LifecycleTransitionEvent:
    version: str
    scan_id: int
    timestamp: datetime
    trade_id: str
    symbol: str
    option_type: str
    from_state: str
    to_state: str
    lifecycle_reason: str
    trade_started_at: datetime
    confirmed_at: datetime | None
    fingerprint: SnapshotFingerprint


class LifecycleEventSubscriber(Protocol):
    def __call__(self, event: LifecycleTransitionEvent) -> None: ...


class LifecycleEventPublisher(Protocol):
    def publish(self, event: LifecycleTransitionEvent) -> None: ...
