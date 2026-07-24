import io
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.observability.telegram_notifier import TelegramLifecycleNotifier


class _Response:
    status = 200

    def read(self):
        return b'{"ok": true, "result": {"message_id": 1}}'

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class TelegramLifecycleNotifierTests(unittest.TestCase):
    def test_wait_for_delivery_waits_for_the_worker_result(self):
        notifier = TelegramLifecycleNotifier("token", "chat")
        failure_count = notifier.delivery_failure_count()
        with (
            patch.object(notifier, "_message", return_value="test"),
            patch.object(notifier, "_send", return_value=True),
        ):
            notifier(SimpleNamespace(to_state="EXIT"))
            self.assertTrue(notifier.wait_for_delivery(1, failure_count))

    def test_send_logs_successful_telegram_response(self):
        notifier = TelegramLifecycleNotifier("token", "chat")
        with patch("app.observability.telegram_notifier.urlopen", return_value=_Response()):
            self.assertTrue(notifier._send("test"))

    def test_http_error_is_reported_as_a_failed_delivery(self):
        from urllib.error import HTTPError

        notifier = TelegramLifecycleNotifier("token", "chat")
        error = HTTPError("https://example.test", 400, "Bad Request", {}, io.BytesIO(b'{"ok": false}'))
        with patch("app.observability.telegram_notifier.urlopen", side_effect=error):
            self.assertFalse(notifier._send("test"))
