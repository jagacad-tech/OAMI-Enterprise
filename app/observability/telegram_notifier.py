"""Asynchronous, read-only Telegram lifecycle notification subscriber."""

import json
import queue
import threading
import time
from dataclasses import dataclass
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app.core.logger import logger


@dataclass
class _Notification:
    message: str
    delivered: bool | None = None


class TelegramLifecycleNotifier:
    NOTIFIED_STATES = {"NEW BUY", "CONFIRMED", "WEAKENING", "EXIT"}

    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self._notifications = queue.Queue()
        self._delivery_condition = threading.Condition()
        self._submitted_count = 0
        self._completed_count = 0
        self._failed_count = 0
        self._worker = threading.Thread(
            target=self._run,
            name="oami-telegram-notifier",
            daemon=True,
        )
        self._worker.start()

    def __call__(self, event):
        if event.to_state not in self.NOTIFIED_STATES:
            return
        notification = _Notification(self._message(event))
        with self._delivery_condition:
            self._submitted_count += 1
        self._notifications.put(notification)

    def delivery_failure_count(self):
        """Return a marker that can be passed to ``wait_for_delivery``."""
        with self._delivery_condition:
            return self._failed_count

    def wait_for_delivery(self, timeout=10, failures_before=0):
        """Wait for notifications already queued by this notifier.

        This is intended for finite developer commands such as the observability
        self-test. The scanner never calls it, so Telegram remains asynchronous
        during normal market processing.
        """
        deadline = time.monotonic() + timeout
        with self._delivery_condition:
            submitted_count = self._submitted_count
            while self._completed_count < submitted_count:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False
                self._delivery_condition.wait(remaining)
            return self._failed_count == failures_before

    def _run(self):
        while True:
            notification = self._notifications.get()
            try:
                notification.delivered = self._send(notification.message)
            except Exception:
                # Keep the worker alive even if a future sender implementation
                # unexpectedly raises outside of _send's HTTP handling.
                logger.exception("Telegram lifecycle worker failed")
                notification.delivered = False
            finally:
                with self._delivery_condition:
                    self._completed_count += 1
                    if not notification.delivered:
                        self._failed_count += 1
                    self._delivery_condition.notify_all()
                self._notifications.task_done()

    def _message(self, event):
        value = event.fingerprint
        return (
            f"OAMI {event.version}\n"
            f"{event.to_state} | {event.symbol} {event.option_type}\n"
            f"Trade {event.trade_id} | Scan {event.scan_id}\n"
            f"Score {value.score} | Conf {value.confidence} | {value.trend}/{value.momentum}\n"
            f"RVOL {value.rvol:.2f} | OBI {value.obi:.2f} | Spread {value.spread:.4f}\n"
            f"Reason: {event.lifecycle_reason}"
        )

    def _send(self, message):
        try:
            body = json.dumps({"chat_id": self.chat_id, "text": message}).encode("utf-8")
            request = Request(
                f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=5) as response:
                status_code = response.status
                response_body = response.read().decode("utf-8", errors="replace")
            try:
                response_json = json.loads(response_body)
            except json.JSONDecodeError:
                response_json = {"raw_body": response_body}

            logger.info(
                "Telegram lifecycle notification response: status_code=%s json=%s",
                status_code,
                response_json,
            )
            if status_code == 200 and response_json.get("ok") is True:
                return True

            logger.error(
                "Telegram lifecycle notification was rejected: status_code=%s json=%s",
                status_code,
                response_json,
            )
        except HTTPError as error:
            response_body = error.read().decode("utf-8", errors="replace")
            try:
                response_json = json.loads(response_body)
            except json.JSONDecodeError:
                response_json = {"raw_body": response_body}
            logger.error(
                "Telegram lifecycle notification response: status_code=%s json=%s",
                error.code,
                response_json,
            )
        except Exception:
            logger.exception("Telegram lifecycle notification failed")
        return False
