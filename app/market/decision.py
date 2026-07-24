"""
OAMI Enterprise
Decision Engine V2
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class EntryAssessment:
    qualified: bool
    option_type: str | None
    reason: str


@dataclass(frozen=True)
class ExitAssessment:
    hard_exit: bool
    soft_exit: bool
    reason: str


class DecisionEngine:

    MINIMUM_SCORE = 65
    MINIMUM_CONFIDENCE = 65

    def analyze(self, snapshot):

        snapshot.signal = "WAIT"
        snapshot.action = "NO TRADE"
        snapshot.setup_quality = self.setup_quality(snapshot.score)

        bullish = self.is_bullish_confirmation(snapshot)
        bearish = self.is_bearish_confirmation(snapshot)
        spread_ok = self.is_spread_acceptable(snapshot)

        snapshot.confidence = self.adjust_confidence(
            snapshot,
            bullish=bullish,
            bearish=bearish,
            spread_ok=spread_ok,
        )

        entry = self.evaluate_entry(snapshot)

        if entry.qualified:
            snapshot.signal = "BUY"
            snapshot.action = f"BUY {entry.option_type}"
            snapshot.decision_reason = entry.reason

        elif snapshot.trend in {"BULLISH", "BEARISH"}:
            snapshot.signal = "WATCH"
            snapshot.action = (
                "WATCH CE" if snapshot.trend == "BULLISH" else "WATCH PE"
            )
            snapshot.decision_reason = self.watch_reason(
                snapshot,
                bullish=bullish,
                bearish=bearish,
                spread_ok=spread_ok,
            )

        else:
            snapshot.decision_reason = self.no_trade_reason(snapshot, spread_ok)

        return snapshot

    def evaluate_entry(self, snapshot):
        """Stateless answer to: should a new trade be entered now?"""
        bullish = self.is_bullish_confirmation(snapshot)
        bearish = self.is_bearish_confirmation(snapshot)
        spread_ok = self.is_spread_acceptable(snapshot)

        if bullish and spread_ok and self.qualified(snapshot):
            return EntryAssessment(True, "CE", self.buy_reason(snapshot, "Bullish"))
        if bearish and spread_ok and self.qualified(snapshot):
            return EntryAssessment(True, "PE", self.buy_reason(snapshot, "Bearish"))

        return EntryAssessment(
            False,
            None,
            self.watch_reason(snapshot, bullish, bearish, spread_ok)
            if snapshot.trend in {"BULLISH", "BEARISH"}
            else self.no_trade_reason(snapshot, spread_ok),
        )

    def evaluate_exit(self, snapshot, option_type):
        """Stateless answer to: should an active trade continue to be held?"""
        expected_trend = "BULLISH" if option_type == "CE" else "BEARISH"
        opposing_trend = "BEARISH" if option_type == "CE" else "BULLISH"

        if snapshot.trend == opposing_trend:
            return ExitAssessment(True, False, f"Trend reversed to {opposing_trend}")

        if self.flow_conflicts_with_trend(snapshot):
            return ExitAssessment(False, True, "Order flow conflicts with trend")

        if snapshot.trend != expected_trend:
            return ExitAssessment(False, True, "Directional trend lost")

        if snapshot.confidence < self.MINIMUM_CONFIDENCE or snapshot.score < self.MINIMUM_SCORE:
            return ExitAssessment(False, True, "Score or confidence weakened")

        return ExitAssessment(False, False, "Holding criteria remain valid")

    # -------------------------------------------------

    def is_bullish_confirmation(self, snapshot):
        return (
            snapshot.trend == "BULLISH"
            and snapshot.momentum in {"MEDIUM", "STRONG"}
            and snapshot.orderbook_imbalance >= 0.10
            and snapshot.bid_pressure > snapshot.ask_pressure
        )

    def is_bearish_confirmation(self, snapshot):
        return (
            snapshot.trend == "BEARISH"
            and snapshot.momentum in {"MEDIUM", "STRONG"}
            and snapshot.orderbook_imbalance <= -0.10
            and snapshot.ask_pressure > snapshot.bid_pressure
        )

    def qualified(self, snapshot):
        return (
            snapshot.score >= self.MINIMUM_SCORE
            and snapshot.confidence >= self.MINIMUM_CONFIDENCE
        )

    # -------------------------------------------------

    def adjust_confidence(self, snapshot, bullish, bearish, spread_ok):
        confidence = snapshot.score
        aligned = bullish or bearish
        has_depth = snapshot.depth is not None

        if aligned:
            confidence += 15
        elif self.flow_conflicts_with_trend(snapshot):
            confidence -= 25
        elif has_depth:
            confidence -= 10
        else:
            confidence -= 10

        if not spread_ok:
            confidence -= 15

        if snapshot.rvol < 1.3:
            confidence -= 5

        return max(0, min(100, confidence))

    # -------------------------------------------------

    def is_spread_acceptable(self, snapshot):
        if snapshot.spread <= 0:
            return False

        return snapshot.spread <= self.spread_limit(snapshot)

    def spread_limit(self, snapshot):
        """Instrument-specific defaults isolated for future tuning."""

        limits = {
            "INDEX": 0.0005,
            "STOCK": 0.0010,
        }

        percentage_limit = limits.get(snapshot.instrument_type, 0.0010)
        reference_price = max(snapshot.ltp, 1.0)

        return reference_price * percentage_limit

    # -------------------------------------------------

    def flow_conflicts_with_trend(self, snapshot):
        return (
            (snapshot.trend == "BULLISH" and snapshot.orderbook_imbalance < -0.10)
            or (snapshot.trend == "BEARISH" and snapshot.orderbook_imbalance > 0.10)
        )

    def setup_quality(self, score):
        if score >= 90:
            return "A+"
        if score >= 75:
            return "A"
        if score >= 60:
            return "B"
        return "C"

    # -------------------------------------------------

    def buy_reason(self, snapshot, direction):
        flow = "Strong Order Flow" if abs(snapshot.orderbook_imbalance) >= 0.30 else "Order Flow"
        volume = "RVOL Confirmed" if snapshot.rvol >= 2.0 else "RVOL Building"
        return f"{direction} Trend + {snapshot.momentum.title()} Momentum + {flow} + {volume}"

    def watch_reason(self, snapshot, bullish, bearish, spread_ok):
        if not spread_ok:
            return "Wide Spread or Missing Depth"
        if self.flow_conflicts_with_trend(snapshot):
            return "Trend/Order Flow Conflict"
        if not (bullish or bearish):
            return "Weak Order Flow"
        if snapshot.confidence < self.MINIMUM_CONFIDENCE:
            return "Low Confidence"
        if snapshot.score < self.MINIMUM_SCORE:
            return "Score Building"
        if snapshot.rvol < 1.3:
            return "RVOL Building"
        return "Confirmation Building"

    def no_trade_reason(self, snapshot, spread_ok):
        if not spread_ok and snapshot.depth is not None:
            return "Wide Spread"
        if snapshot.depth is None:
            return "Missing Depth"
        if snapshot.momentum == "LOW":
            return "No Directional Momentum"
        return "No Directional Trend"
