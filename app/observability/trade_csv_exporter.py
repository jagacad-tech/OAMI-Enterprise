"""Read-only completed-trade CSV exporter."""

import csv
from dataclasses import asdict, fields
from pathlib import Path

from app.observability.trade_summary import CompletedTradeSummary, TradeSummaryBuilder


class CompletedTradeCsvExporter:
    def __init__(self, path):
        self.path = Path(path)
        self._builder = TradeSummaryBuilder()

    def __call__(self, event):
        summary = self._builder.consume(event)
        if not summary:
            return

        self.path.parent.mkdir(parents=True, exist_ok=True)
        write_header = not self.path.exists() or self.path.stat().st_size == 0
        with self.path.open("a", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(
                output,
                fieldnames=[field.name for field in fields(CompletedTradeSummary)],
            )
            if write_header:
                writer.writeheader()
            writer.writerow(asdict(summary))
