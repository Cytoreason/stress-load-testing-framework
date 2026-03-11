"""
Metrics collection and percentile computation.

Attaches to Locust's ``request`` event and accumulates per-name response
times so percentiles (p90, p95, p99) can be computed at end-of-run and
exported via reporter.py.

Design:
- Thread-safe using a threading.Lock (Locust workers emit events from
  multiple greenlets; gevent monkey-patches threading).
- Samples are stored as raw millisecond integers in a deque with a cap
  so memory stays bounded even for very long runs.
- Summary statistics are emitted per request name AND in aggregate.
"""
from __future__ import annotations

import statistics
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any

# Maximum number of raw samples per event name.
# 10_000 per name × ~50 distinct names = ~500k entries (~4 MB) – acceptable.
_MAX_SAMPLES_PER_NAME: int = 10_000


@dataclass
class NamedStats:
    """Per-name aggregated statistics."""

    name: str
    total_requests: int = 0
    total_failures: int = 0
    _samples: deque = field(default_factory=lambda: deque(maxlen=_MAX_SAMPLES_PER_NAME))
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def record(self, response_time_ms: float, *, failed: bool = False) -> None:
        with self._lock:
            self.total_requests += 1
            if failed:
                self.total_failures += 1
            else:
                self._samples.append(response_time_ms)

    def summary(self) -> dict[str, Any]:
        with self._lock:
            samples = list(self._samples)

        if not samples:
            return {
                "name": self.name,
                "total_requests": self.total_requests,
                "total_failures": self.total_failures,
                "failure_rate_pct": self._failure_rate(),
                "avg_ms": None,
                "median_ms": None,
                "max_ms": None,
                "p90_ms": None,
                "p95_ms": None,
                "p99_ms": None,
            }

        sorted_s = sorted(samples)
        return {
            "name": self.name,
            "total_requests": self.total_requests,
            "total_failures": self.total_failures,
            "failure_rate_pct": self._failure_rate(),
            "avg_ms": round(statistics.mean(samples), 1),
            "median_ms": round(statistics.median(sorted_s), 1),
            "max_ms": round(sorted_s[-1], 1),
            "p90_ms": round(_percentile(sorted_s, 90), 1),
            "p95_ms": round(_percentile(sorted_s, 95), 1),
            "p99_ms": round(_percentile(sorted_s, 99), 1),
        }

    def _failure_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return round(self.total_failures / self.total_requests * 100, 2)


class MetricsCollector:
    """
    Central collector that listens to Locust's request event and aggregates
    per-name and overall statistics.

    Usage (in locustfile)::

        collector = MetricsCollector()
        collector.attach(environment)
    """

    def __init__(self) -> None:
        self._stats: dict[str, NamedStats] = defaultdict(
            lambda: NamedStats(name="<unknown>")
        )
        self._lock = threading.Lock()

    def attach(self, environment: Any) -> None:
        """Bind the collector to a Locust environment."""
        environment.events.request.add_listener(self._on_request)

    def _on_request(
        self,
        *,
        request_type: str,
        name: str,
        response_time: float,
        exception: BaseException | None,
        **_kwargs: Any,
    ) -> None:
        with self._lock:
            if name not in self._stats:
                self._stats[name] = NamedStats(name=name)
            entry = self._stats[name]

        entry.record(response_time, failed=exception is not None)

    def all_summaries(self) -> list[dict[str, Any]]:
        """Return a list of per-name summary dicts, sorted by name."""
        with self._lock:
            names = list(self._stats.keys())
        return sorted(
            (self._stats[n].summary() for n in names), key=lambda s: s["name"]
        )

    def aggregate_summary(self) -> dict[str, Any]:
        """Return a single summary across ALL event names."""
        all_samples: list[float] = []
        total_reqs = 0
        total_fails = 0

        with self._lock:
            entries = list(self._stats.values())

        for entry in entries:
            with entry._lock:
                all_samples.extend(list(entry._samples))
            total_reqs += entry.total_requests
            total_fails += entry.total_failures

        if not all_samples:
            return {
                "name": "__AGGREGATE__",
                "total_requests": total_reqs,
                "total_failures": total_fails,
                "failure_rate_pct": 0.0,
                "avg_ms": None,
                "median_ms": None,
                "max_ms": None,
                "p90_ms": None,
                "p95_ms": None,
                "p99_ms": None,
            }

        sorted_s = sorted(all_samples)
        failure_rate = round(total_fails / total_reqs * 100, 2) if total_reqs else 0.0
        return {
            "name": "__AGGREGATE__",
            "total_requests": total_reqs,
            "total_failures": total_fails,
            "failure_rate_pct": failure_rate,
            "avg_ms": round(statistics.mean(all_samples), 1),
            "median_ms": round(statistics.median(sorted_s), 1),
            "max_ms": round(sorted_s[-1], 1),
            "p90_ms": round(_percentile(sorted_s, 90), 1),
            "p95_ms": round(_percentile(sorted_s, 95), 1),
            "p99_ms": round(_percentile(sorted_s, 99), 1),
        }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _percentile(sorted_samples: list[float], pct: float) -> float:
    """
    Linear interpolation percentile (matches numpy's default method).
    *sorted_samples* must already be sorted ascending.
    """
    if not sorted_samples:
        return 0.0
    n = len(sorted_samples)
    idx = (pct / 100) * (n - 1)
    lo = int(idx)
    hi = lo + 1
    if hi >= n:
        return sorted_samples[-1]
    frac = idx - lo
    return sorted_samples[lo] + frac * (sorted_samples[hi] - sorted_samples[lo])
