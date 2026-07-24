# Product Backlog

Items below are deliberately deferred until Sprint 2B has completed live
observation and its thresholds have been reviewed.

## Composite Trend Engine

**Goal:** Replace the single open-versus-LTP trend classification with a
multi-signal directional assessment.

**Scope:** Combine price structure, momentum, volume, and order-flow inputs;
publish direction, strength, and an explainable trend reason without changing
the scanner orchestration.

**Acceptance criteria:** The engine reports its component inputs and reason,
has deterministic tests for bullish/bearish/neutral cases, and improves on the
Sprint 2B observation baseline without increasing churn.

## Hard Exit vs Soft Exit Logic

**Goal:** Classify invalidation conditions explicitly and tune exit hysteresis
from observed data.

**Scope:** Define hard exits (immediate) and soft exits (grace scans), with
per-condition reasons and configurable thresholds.

**Acceptance criteria:** Each exit is labelled hard or soft, soft exits respect
the configured grace period, and validation reporting compares premature exits
with avoided losses.

## Market Open Filter

**Goal:** Prevent early-session volatility and incomplete depth from producing
low-quality lifecycle entries.

**Scope:** Add a configurable market-open observation/filter window that
suppresses new entries while retaining transparent reasons.

**Acceptance criteria:** No new BUY is published inside the configured window;
the dashboard/log identifies the filter; behavior is covered for normal and
delayed market-data sessions.

## Market Regime Engine

**Goal:** Classify the broader market as trending, range-bound, high-volatility,
or otherwise unsuitable, then provide context to entry and exit policy.

**Scope:** Use index breadth, volatility, RVOL, and directional participation
to publish a regime and confidence; do not embed regime decisions in the
dashboard.

**Acceptance criteria:** Regime output is explainable and tested, lifecycle
policy consumes it through a clear interface, and live validation demonstrates
when the filter helps versus when it suppresses valid trades.

## Sprint 2B.3 – Asynchronous Observability

**Goal:** Ensure observability outputs can never delay the scanner thread.

**Scope:** Replace synchronous lifecycle subscriber execution with a queued
background worker for compact logs, trade summaries, CSV export, and Telegram
notifications. Preserve immutable event contracts and failure isolation.

**Prerequisite:** Complete several live observation sessions and measure
transition-time latency before adding this concurrency complexity.

**Acceptance criteria:** Scanner transition processing remains independent of
subscriber latency; queue saturation and subscriber failures are observable;
and no lifecycle, entry, or exit decision is changed by the worker.
