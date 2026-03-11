"""
Metrics reporter.

Exports collected performance data to JSON and/or CSV files at end-of-run.
The output schema matches the requirements:

  Per-name:
    name, total_requests, total_failures, failure_rate_pct,
    avg_ms, median_ms, max_ms, p90_ms, p95_ms, p99_ms

  Plus an __AGGREGATE__ row that rolls up all events.

Integration:
  Attach to Locust's ``quitting`` event so the report is always written even
  if the run is interrupted:

      reporter = PerformanceReporter(collector, settings.artifacts_dir)
      environment.events.quitting.add_listener(reporter.on_quitting)
"""
from __future__ import annotations

import csv
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

from src.config import settings
from src.telemetry.metrics import MetricsCollector

logger = logging.getLogger(__name__)

_COLUMNS = [
    "name",
    "total_requests",
    "total_failures",
    "failure_rate_pct",
    "avg_ms",
    "median_ms",
    "max_ms",
    "p90_ms",
    "p95_ms",
    "p99_ms",
]


class PerformanceReporter:
    """Serialises MetricsCollector snapshots to disk."""

    def __init__(
        self,
        collector: MetricsCollector,
        output_dir: Path | None = None,
        *,
        run_id: str | None = None,
        node_id: str | None = None,
    ) -> None:
        self.collector = collector
        self.output_dir = output_dir or settings.artifacts_dir
        self.run_id = run_id or time.strftime("%Y%m%d_%H%M%S")
        self.node_id = node_id or settings.node_id

    # ------------------------------------------------------------------
    # Locust event hook
    # ------------------------------------------------------------------

    def on_quitting(self, environment: Any, **_kwargs: Any) -> None:
        """Called by Locust when the test run finishes."""
        self.write_report()

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def write_report(self) -> dict[str, Path]:
        """Write JSON and/or CSV report files.  Returns paths written."""
        rows = self.collector.all_summaries()
        rows.append(self.collector.aggregate_summary())

        envelope = {
            "run_id": self.run_id,
            "node_id": self.node_id,
            "profile": settings.test_profile.value,
            "base_url": settings.base_url,
            "peak_users": settings.peak_users,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "results": rows,
        }

        self.output_dir.mkdir(parents=True, exist_ok=True)
        paths: dict[str, Path] = {}
        fmt = settings.report_format.lower()

        if fmt in ("json", "both"):
            json_path = self.output_dir / f"report_{self.run_id}_{self.node_id}.json"
            json_path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
            logger.info("Report written: %s", json_path)
            paths["json"] = json_path

        if fmt in ("csv", "both"):
            csv_path = self.output_dir / f"report_{self.run_id}_{self.node_id}.csv"
            with csv_path.open("w", newline="", encoding="utf-8") as fh:
                writer = csv.DictWriter(fh, fieldnames=_COLUMNS, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(rows)
            logger.info("Report written: %s", csv_path)
            paths["csv"] = csv_path

        return paths

    def print_summary_table(self) -> None:
        """Print a human-readable summary table to stdout."""
        rows = self.collector.all_summaries()
        rows.append(self.collector.aggregate_summary())

        header = (
            f"{'Name':<60} {'Reqs':>6} {'Fails':>6} {'Fail%':>6} "
            f"{'Avg':>7} {'Med':>7} {'Max':>7} {'p90':>7} {'p95':>7} {'p99':>7}"
        )
        print("\n" + "=" * len(header))
        print(header)
        print("-" * len(header))
        for row in rows:
            def _fmt(v: Any) -> str:
                return f"{v:>7.0f}" if isinstance(v, (int, float)) else f"{'N/A':>7}"

            print(
                f"{row['name']:<60} "
                f"{row['total_requests']:>6} "
                f"{row['total_failures']:>6} "
                f"{row['failure_rate_pct']:>5.1f}% "
                f"{_fmt(row['avg_ms'])} "
                f"{_fmt(row['median_ms'])} "
                f"{_fmt(row['max_ms'])} "
                f"{_fmt(row['p90_ms'])} "
                f"{_fmt(row['p95_ms'])} "
                f"{_fmt(row['p99_ms'])}"
            )
        print("=" * len(header) + "\n")
