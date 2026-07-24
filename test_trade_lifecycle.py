import unittest

from app.core.constants import APP_VERSION
from app.market.decision import DecisionEngine
from app.market.models import MarketSnapshot
from app.market.option_selector import OptionSelector
from app.market.trade_lifecycle import TradeLifecycleEngine
from app.observability.event_bus import LifecycleEventBus
from app.observability.trade_summary import TradeSummaryBuilder


def bullish_snapshot():
    return MarketSnapshot(
        symbol="RELIANCE",
        ltp=100.0,
        open=99.0,
        high=102.0,
        low=98.0,
        close=99.0,
        trend="BULLISH",
        momentum="MEDIUM",
        score=75,
        confidence=75,
        rvol=1.5,
        spread=0.05,
        instrument_type="STOCK",
        depth={},
        bid_pressure=200,
        ask_pressure=100,
        orderbook_imbalance=0.20,
        option_type="CE",
    )


class TradeLifecycleEngineTests(unittest.TestCase):
    def setUp(self):
        self.decision = DecisionEngine()
        self.lifecycle = TradeLifecycleEngine(self.decision)

    def scan(self, snapshot):
        return self.lifecycle.analyze(self.decision.analyze(snapshot))

    def test_entry_is_confirmed_after_two_qualifying_scans(self):
        first = self.scan(bullish_snapshot())
        second = self.scan(bullish_snapshot())

        self.assertEqual(first.lifecycle_state, "NEW BUY")
        self.assertEqual(second.lifecycle_state, "CONFIRMED")
        self.assertEqual(second.action, "BUY CE")
        self.assertIn("held for 2 scans", second.lifecycle_reason)

    def test_one_soft_exit_scan_does_not_exit_trade(self):
        self.scan(bullish_snapshot())
        self.scan(bullish_snapshot())
        weakened = bullish_snapshot()
        weakened.bid_pressure = 100
        weakened.ask_pressure = 200
        weakened.orderbook_imbalance = -0.20

        result = self.scan(weakened)

        self.assertEqual(result.lifecycle_state, "WEAKENING")
        self.assertEqual(result.action, "HOLD CE")
        self.assertIn("grace scan 1 of 2", result.lifecycle_reason)

    def test_new_buy_survives_one_non_qualifying_scan(self):
        self.scan(bullish_snapshot())
        weakened = bullish_snapshot()
        weakened.bid_pressure = 100
        weakened.ask_pressure = 200
        weakened.orderbook_imbalance = -0.20

        result = self.scan(weakened)

        self.assertEqual(result.lifecycle_state, "NEW BUY")
        self.assertEqual(result.action, "BUY CE")
        self.assertIn("grace scan 1 of 2", result.lifecycle_reason)

    def test_second_soft_exit_scan_exits_trade(self):
        self.scan(bullish_snapshot())
        self.scan(bullish_snapshot())
        weakened = bullish_snapshot()
        weakened.bid_pressure = 100
        weakened.ask_pressure = 200
        weakened.orderbook_imbalance = -0.20
        self.scan(weakened)

        result = self.scan(weakened)

        self.assertEqual(result.lifecycle_state, "EXIT")
        self.assertEqual(result.action, "EXIT CE")

    def test_transition_event_has_version_scan_id_trade_id_and_fingerprint(self):
        events = []
        bus = LifecycleEventBus()
        bus.subscribe(events.append)
        lifecycle = TradeLifecycleEngine(self.decision, bus)

        lifecycle.analyze(self.decision.analyze(bullish_snapshot()), scan_id=42)

        event = events[0]
        self.assertEqual(event.version, APP_VERSION)
        self.assertEqual(event.scan_id, 42)
        self.assertTrue(event.trade_id.startswith("T-RELIANCE-"))
        self.assertEqual(event.to_state, "NEW BUY")
        self.assertEqual(event.fingerprint.score, 75)
        self.assertEqual(event.fingerprint.rvol, 1.5)
        self.assertEqual(event.fingerprint.bid_pressure, 200)
        self.assertEqual(event.fingerprint.ask_pressure, 100)
        self.assertEqual(event.fingerprint.lifecycle_reason, event.lifecycle_reason)

    def test_trade_ids_are_unique_across_lifecycle_engine_restarts(self):
        first = TradeLifecycleEngine(self.decision)
        second = TradeLifecycleEngine(self.decision)

        first.analyze(self.decision.analyze(bullish_snapshot()))
        second.analyze(self.decision.analyze(bullish_snapshot()))

        first_id = first.records["RELIANCE"].trade_id
        second_id = second.records["RELIANCE"].trade_id
        self.assertNotEqual(first_id, second_id)
        self.assertTrue(first_id.startswith("T-RELIANCE-"))
        self.assertTrue(second_id.startswith("T-RELIANCE-"))

    def test_completed_exit_summary_has_highest_metrics(self):
        summaries = []
        builder = TradeSummaryBuilder()
        bus = LifecycleEventBus()
        bus.subscribe(lambda event: summaries.append(builder.consume(event)))
        lifecycle = TradeLifecycleEngine(self.decision, bus)

        lifecycle.analyze(self.decision.analyze(bullish_snapshot()), scan_id=1)
        lifecycle.analyze(self.decision.analyze(bullish_snapshot()), scan_id=2)
        weakened = bullish_snapshot()
        weakened.bid_pressure = 100
        weakened.ask_pressure = 200
        weakened.orderbook_imbalance = -0.20
        lifecycle.analyze(self.decision.analyze(weakened), scan_id=3)
        lifecycle.analyze(self.decision.analyze(weakened), scan_id=4)

        summary = summaries[-1]
        self.assertEqual(summary.highest_score, 75)
        self.assertEqual(summary.highest_confidence, 90)
        self.assertEqual(summary.transition_count, 4)


class OptionSelectorTests(unittest.TestCase):
    def test_missing_chain_never_fabricates_strike(self):
        snapshot = bullish_snapshot()
        snapshot.lifecycle_state = "CONFIRMED"
        result = OptionSelector(lambda symbol: []).analyze(snapshot)

        self.assertEqual(result.strike, "-")
        self.assertEqual(result.option_symbol, "-")
        self.assertEqual(result.option_reason, "No validated option chain available")

    def test_nearest_valid_chain_contract_is_recommended(self):
        snapshot = bullish_snapshot()
        snapshot.lifecycle_state = "CONFIRMED"
        selector = OptionSelector(lambda symbol: [
            {
                "option_type": "CE",
                "strike": 95,
                "expiry": "2026-07-23",
                "symbol": "RELIANCE26JUL95CE",
            },
            {
                "option_type": "CE",
                "strike": 105,
                "expiry": "2026-07-23",
                "symbol": "RELIANCE26JUL105CE",
            },
        ])

        result = selector.analyze(snapshot)

        self.assertEqual(result.strike, "95 CE")
        self.assertEqual(result.option_symbol, "RELIANCE26JUL95CE")


if __name__ == "__main__":
    unittest.main()
