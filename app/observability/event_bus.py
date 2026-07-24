"""Failure-isolated lifecycle event dispatcher."""

from app.core.logger import logger


class LifecycleEventBus:
    def __init__(self):
        self._subscribers = []
        self._event_count = 0

    @property
    def event_count(self):
        return self._event_count

    def subscribe(self, subscriber):
        self._subscribers.append(subscriber)

    def publish(self, event):
        self._event_count += 1
        for subscriber in tuple(self._subscribers):
            try:
                subscriber(event)
            except Exception:
                logger.exception(
                    "Lifecycle observability subscriber failed: %s",
                    type(subscriber).__name__,
                )

    def close(self):
        """Flush passive subscribers after lifecycle production has stopped."""
        for subscriber in tuple(self._subscribers):
            close = getattr(subscriber, "close", None)
            if close is None:
                continue
            try:
                close()
            except Exception:
                logger.exception(
                    "Lifecycle observability subscriber close failed: %s",
                    type(subscriber).__name__,
                )

    def status(self):
        """Expose health telemetry from passive subscribers that support it."""
        return {
            type(subscriber).__name__: subscriber.status()
            for subscriber in tuple(self._subscribers)
            if callable(getattr(subscriber, "status", None))
        }
