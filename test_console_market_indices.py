"""Console dashboard coverage for the passive Market Indices section."""

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from app.dashboard.console import ConsoleDashboard


class StaticIndexFeed:
    def __init__(self, indices):
        self.indices = indices

    def latest(self):
        return self.indices


class ConsoleMarketIndicesTests(unittest.TestCase):
    market = {
        "state": "UNKNOWN",
        "avg_score": 0,
        "avg_rvol": 0,
        "bullish": 0,
        "bearish": 0,
        "neutral": 0,
    }

    def render(self, indices):
        output = io.StringIO()
        dashboard = ConsoleDashboard(StaticIndexFeed(indices))
        with patch("app.dashboard.console.os.system"), redirect_stdout(output):
            dashboard.show([], self.market)
        return output.getvalue()

    def test_displays_passive_index_value_and_trend(self):
        output = self.render(
            [
                {"symbol": "NIFTY", "value": 22100.5, "trend": "BULLISH"},
                {"symbol": "BANKNIFTY", "value": 48000, "trend": "BEARISH"},
                {"symbol": "FINNIFTY", "value": 21000, "trend": "NEUTRAL"},
                {"symbol": "SENSEX", "value": 73000, "trend": "BULLISH"},
            ]
        )

        self.assertIn("Market Indices (Passive Feed)", output)
        self.assertIn("NIFTY", output)
        self.assertIn("BANKNIFTY", output)
        self.assertIn("FINNIFTY", output)
        self.assertIn("SENSEX", output)
        self.assertIn("22,100.50", output)
        self.assertIn("Bullish", output)
        self.assertIn("Bearish", output)
        self.assertIn("Neutral", output)

    def test_waits_when_the_passive_index_feed_has_no_data(self):
        output = self.render([])

        self.assertIn("Market Indices (Passive Feed)", output)
        self.assertIn("Waiting for index data...", output)


if __name__ == "__main__":
    unittest.main()
