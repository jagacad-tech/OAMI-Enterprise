"""Compact read-only lifecycle transition log subscriber."""

from app.core.logger import logger


class CompactLifecycleLogger:
    def __call__(self, event):
        fingerprint = event.fingerprint
        logger.info(
            "LIFECYCLE v=%s scan=%s trade=%s %s %s->%s "
            "score=%s conf=%s trend=%s mom=%s rvol=%.2f obi=%.2f "
            "bid=%s ask=%s spread=%.4f reason=%s",
            event.version,
            event.scan_id,
            event.trade_id,
            event.symbol,
            event.from_state,
            event.to_state,
            fingerprint.score,
            fingerprint.confidence,
            fingerprint.trend,
            fingerprint.momentum,
            fingerprint.rvol,
            fingerprint.obi,
            fingerprint.bid_pressure,
            fingerprint.ask_pressure,
            fingerprint.spread,
            event.lifecycle_reason,
        )
