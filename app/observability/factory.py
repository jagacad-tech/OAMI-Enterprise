"""Application wiring for passive lifecycle observability subscribers."""

import os

from app.core.config import settings
from app.core.logger import logger
from app.observability.event_bus import LifecycleEventBus
from app.observability.lifecycle_logger import CompactLifecycleLogger
from app.observability.telegram_notifier import TelegramLifecycleNotifier
from app.observability.trade_csv_exporter import CompletedTradeCsvExporter
from app.observability.trade_summary import TradeSummaryLogger
from app.observability.trade_intelligence import TradeIntelligenceLogger
from app.observability.market_session import MarketSessionRecorder


def build_lifecycle_event_bus(config=None):
    """Build the passive lifecycle event bus.

    An explicit configuration lets developer tools use the production
    subscribers with an isolated output path, without changing app settings.
    """
    config = settings.observability if config is None else config
    bus = LifecycleEventBus()

    if config.get("lifecycle_log_enabled", True):
        bus.subscribe(CompactLifecycleLogger())
    if config.get("trade_summary_enabled", True):
        bus.subscribe(TradeSummaryLogger())
    if config.get("csv_export_enabled", False):
        bus.subscribe(CompletedTradeCsvExporter(config["completed_trades_path"]))
    if config.get("trade_intelligence_enabled", True):
        bus.subscribe(
            TradeIntelligenceLogger(
                config.get("analytics_database_path", "data/oami_analytics.sqlite3")
            )
        )
    if config.get("telegram_enabled", False):
        token = os.getenv(config.get("bot_token_env", "TELEGRAM_BOT_TOKEN"))
        chat_id = os.getenv(config.get("chat_id_env", "TELEGRAM_CHAT_ID"))
        if token and chat_id:
            bus.subscribe(TelegramLifecycleNotifier(token, chat_id))
        else:
            logger.warning(
                "Telegram observability disabled: one or both configured environment variables are missing"
            )

    return bus


def build_market_session_recorder(config=None):
    """Build the independent index analytics recorder, if enabled."""
    config = settings.observability if config is None else config
    if not config.get("market_session_enabled", True):
        return None
    return MarketSessionRecorder(
        config.get("analytics_database_path", "data/oami_analytics.sqlite3"),
        config.get("market_session_min_capture_interval_seconds", 1.0),
    )
