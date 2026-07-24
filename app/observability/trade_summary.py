"""Read-only completed-trade summary construction."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CompletedTradeSummary:
    version: str
    trade_id: str
    symbol: str
    option_type: str
    started_at: str
    confirmed_at: str
    exited_at: str
    duration_seconds: int
    entry_ltp: float
    exit_ltp: float
    underlying_change_pct: float
    entry_score: int
    entry_confidence: int
    exit_score: int
    exit_confidence: int
    highest_score: int
    highest_confidence: int
    exit_reason: str
    transition_count: int


class TradeSummaryBuilder:
    """Maintains read-only event history per trade until an EXIT arrives."""

    def __init__(self):
        self._trades = {}

    def consume(self, event):
        trade = self._trades.get(event.trade_id)
        if trade is None:
            if event.to_state != "NEW BUY":
                return None
            trade = {
                "entry": event,
                "highest_score": event.fingerprint.score,
                "highest_confidence": event.fingerprint.confidence,
                "transition_count": 0,
            }
            self._trades[event.trade_id] = trade
        trade["highest_score"] = max(trade["highest_score"], event.fingerprint.score)
        trade["highest_confidence"] = max(
            trade["highest_confidence"], event.fingerprint.confidence
        )
        trade["transition_count"] += 1

        if event.to_state == "INVALID":
            del self._trades[event.trade_id]
            return None

        if event.to_state != "EXIT":
            return None

        entry = trade["entry"]
        change_pct = 0.0
        if entry.fingerprint.ltp:
            change_pct = round(
                ((event.fingerprint.ltp - entry.fingerprint.ltp) / entry.fingerprint.ltp) * 100,
                2,
            )
        summary = CompletedTradeSummary(
            version=event.version,
            trade_id=event.trade_id,
            symbol=event.symbol,
            option_type=event.option_type,
            started_at=event.trade_started_at.isoformat(timespec="seconds"),
            confirmed_at=(
                event.confirmed_at.isoformat(timespec="seconds")
                if event.confirmed_at else ""
            ),
            exited_at=event.timestamp.isoformat(timespec="seconds"),
            duration_seconds=int((event.timestamp - event.trade_started_at).total_seconds()),
            entry_ltp=entry.fingerprint.ltp,
            exit_ltp=event.fingerprint.ltp,
            underlying_change_pct=change_pct,
            entry_score=entry.fingerprint.score,
            entry_confidence=entry.fingerprint.confidence,
            exit_score=event.fingerprint.score,
            exit_confidence=event.fingerprint.confidence,
            highest_score=trade["highest_score"],
            highest_confidence=trade["highest_confidence"],
            exit_reason=event.lifecycle_reason,
            transition_count=trade["transition_count"],
        )
        del self._trades[event.trade_id]
        return summary


class TradeSummaryLogger:
    def __init__(self):
        self._builder = TradeSummaryBuilder()

    def __call__(self, event):
        from app.core.logger import logger

        summary = self._builder.consume(event)
        if summary:
            logger.info(
                "TRADE SUMMARY v=%s trade=%s %s %s duration=%ss "
                "ltp=%.2f->%.2f change=%.2f%% max_score=%s max_conf=%s exit=%s",
                summary.version,
                summary.trade_id,
                summary.symbol,
                summary.option_type,
                summary.duration_seconds,
                summary.entry_ltp,
                summary.exit_ltp,
                summary.underlying_change_pct,
                summary.highest_score,
                summary.highest_confidence,
                summary.exit_reason,
            )
