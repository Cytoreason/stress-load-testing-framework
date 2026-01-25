"""
Metrics collection and computation for UI load testing.

Provides thread-safe metrics collection with percentile calculations.
"""

from __future__ import annotations

import asyncio
import json
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator


class EventType(str, Enum):
    """Types of events that can be recorded."""

    STEP_START = "step_start"
    STEP_END = "step_end"
    STEP_ERROR = "step_error"
    ITERATION_START = "iteration_start"
    ITERATION_END = "iteration_end"
    ITERATION_ERROR = "iteration_error"
    USER_START = "user_start"
    USER_END = "user_end"


@dataclass
class StepMetric:
    """Individual step timing record."""

    user_id: int
    iteration: int
    step_name: str
    start_time: float
    end_time: float
    duration_ms: float
    success: bool
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "user_id": self.user_id,
            "iteration": self.iteration,
            "step_name": self.step_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error": self.error,
        }


@dataclass
class UserResult:
    """Results for a single virtual user."""

    user_id: int
    iterations_completed: int = 0
    iterations_failed: int = 0
    start_time: float | None = None
    end_time: float | None = None
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "user_id": self.user_id,
            "iterations_completed": self.iterations_completed,
            "iterations_failed": self.iterations_failed,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": (self.end_time - self.start_time) if self.start_time and self.end_time else None,
            "errors": self.errors,
        }


@dataclass
class StepStats:
    """Aggregated statistics for a step."""

    name: str
    count: int
    success_count: int
    failure_count: int
    min_ms: float
    max_ms: float
    mean_ms: float
    p50_ms: float
    p90_ms: float
    p95_ms: float
    p99_ms: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "count": self.count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "error_rate": self.failure_count / self.count if self.count > 0 else 0,
            "min_ms": round(self.min_ms, 2),
            "max_ms": round(self.max_ms, 2),
            "mean_ms": round(self.mean_ms, 2),
            "p50_ms": round(self.p50_ms, 2),
            "p90_ms": round(self.p90_ms, 2),
            "p95_ms": round(self.p95_ms, 2),
            "p99_ms": round(self.p99_ms, 2),
        }


def compute_percentile(sorted_values: list[float], percentile: float) -> float:
    """
    Compute percentile from sorted values.
    
    Uses linear interpolation between closest ranks.
    """
    if not sorted_values:
        return 0.0
    
    n = len(sorted_values)
    if n == 1:
        return sorted_values[0]
    
    # Percentile index (0-based)
    k = (percentile / 100) * (n - 1)
    f = int(k)
    c = f + 1 if f + 1 < n else f
    
    # Linear interpolation
    if f == c:
        return sorted_values[f]
    
    return sorted_values[f] + (k - f) * (sorted_values[c] - sorted_values[f])


class MetricsCollector:
    """
    Thread-safe metrics collector for load test runs.
    
    Collects step timings, user results, and computes aggregated statistics.
    """

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self._lock = asyncio.Lock()
        
        # Storage
        self._step_metrics: list[StepMetric] = []
        self._user_results: dict[int, UserResult] = {}
        self._events: list[dict[str, Any]] = []
        
        # Run metadata
        self._run_start: float | None = None
        self._run_end: float | None = None
        
        # Events file handle (for streaming writes)
        self._events_file: Path | None = None
    
    async def start_run(self) -> None:
        """Mark the start of a test run."""
        async with self._lock:
            self._run_start = time.time()
            self._events_file = self.output_dir / "events.ndjson"
            self._events_file.parent.mkdir(parents=True, exist_ok=True)
            # Clear/create the events file
            self._events_file.write_text("")
    
    async def end_run(self) -> None:
        """Mark the end of a test run."""
        async with self._lock:
            self._run_end = time.time()
    
    async def register_user(self, user_id: int) -> None:
        """Register a new virtual user."""
        async with self._lock:
            self._user_results[user_id] = UserResult(user_id=user_id)
    
    async def user_started(self, user_id: int) -> None:
        """Mark a user as started."""
        async with self._lock:
            if user_id in self._user_results:
                self._user_results[user_id].start_time = time.time()
            await self._write_event(EventType.USER_START, user_id=user_id)
    
    async def user_ended(self, user_id: int) -> None:
        """Mark a user as ended."""
        async with self._lock:
            if user_id in self._user_results:
                self._user_results[user_id].end_time = time.time()
            await self._write_event(EventType.USER_END, user_id=user_id)
    
    async def iteration_started(self, user_id: int, iteration: int) -> None:
        """Mark start of an iteration."""
        await self._write_event(
            EventType.ITERATION_START, user_id=user_id, iteration=iteration
        )
    
    async def iteration_completed(self, user_id: int, iteration: int) -> None:
        """Mark successful completion of an iteration."""
        async with self._lock:
            if user_id in self._user_results:
                self._user_results[user_id].iterations_completed += 1
            await self._write_event(
                EventType.ITERATION_END, user_id=user_id, iteration=iteration, success=True
            )
    
    async def iteration_failed(self, user_id: int, iteration: int, error: str) -> None:
        """Mark failed iteration."""
        async with self._lock:
            if user_id in self._user_results:
                self._user_results[user_id].iterations_failed += 1
                self._user_results[user_id].errors.append(error)
            await self._write_event(
                EventType.ITERATION_ERROR,
                user_id=user_id,
                iteration=iteration,
                success=False,
                error=error,
            )
    
    async def record_step(self, metric: StepMetric) -> None:
        """Record a step timing metric."""
        async with self._lock:
            self._step_metrics.append(metric)
            event_type = EventType.STEP_END if metric.success else EventType.STEP_ERROR
            await self._write_event(
                event_type,
                user_id=metric.user_id,
                iteration=metric.iteration,
                step_name=metric.step_name,
                duration_ms=metric.duration_ms,
                success=metric.success,
                error=metric.error,
            )
    
    async def _write_event(self, event_type: EventType, **data: Any) -> None:
        """Write an event to the ndjson file."""
        event = {
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "event_type": event_type.value,
            **data,
        }
        self._events.append(event)
        
        # Stream to file
        if self._events_file:
            with open(self._events_file, "a") as f:
                f.write(json.dumps(event) + "\n")
    
    def compute_step_stats(self) -> dict[str, StepStats]:
        """Compute aggregated statistics for all steps."""
        # Group metrics by step name
        steps: dict[str, list[StepMetric]] = {}
        for metric in self._step_metrics:
            if metric.step_name not in steps:
                steps[metric.step_name] = []
            steps[metric.step_name].append(metric)
        
        # Compute stats for each step
        stats: dict[str, StepStats] = {}
        for name, metrics in steps.items():
            durations = sorted([m.duration_ms for m in metrics])
            success_count = sum(1 for m in metrics if m.success)
            failure_count = len(metrics) - success_count
            
            stats[name] = StepStats(
                name=name,
                count=len(metrics),
                success_count=success_count,
                failure_count=failure_count,
                min_ms=min(durations) if durations else 0,
                max_ms=max(durations) if durations else 0,
                mean_ms=sum(durations) / len(durations) if durations else 0,
                p50_ms=compute_percentile(durations, 50),
                p90_ms=compute_percentile(durations, 90),
                p95_ms=compute_percentile(durations, 95),
                p99_ms=compute_percentile(durations, 99),
            )
        
        return stats
    
    def compute_summary(
        self,
        run_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Compute complete summary statistics."""
        step_stats = self.compute_step_stats()
        
        # Overall metrics
        total_iterations = sum(r.iterations_completed for r in self._user_results.values())
        total_failures = sum(r.iterations_failed for r in self._user_results.values())
        total_steps = len(self._step_metrics)
        failed_steps = sum(1 for m in self._step_metrics if not m.success)
        
        run_duration = (self._run_end or time.time()) - (self._run_start or time.time())
        
        return {
            "run_metadata": {
                "run_id": run_config.get("run_id"),
                "scenario_name": run_config.get("scenario", {}).get("name"),
                "base_url": run_config.get("base_url"),
                "user_count": run_config.get("load", {}).get("users"),
                "ramp_up_seconds": run_config.get("load", {}).get("ramp_up_seconds"),
                "duration_seconds": run_config.get("load", {}).get("duration_seconds"),
                "start_time": datetime.fromtimestamp(self._run_start).isoformat() if self._run_start else None,
                "end_time": datetime.fromtimestamp(self._run_end).isoformat() if self._run_end else None,
                "actual_duration_seconds": round(run_duration, 2),
            },
            "overall": {
                "total_iterations": total_iterations,
                "failed_iterations": total_failures,
                "iteration_error_rate": round(total_failures / max(total_iterations + total_failures, 1), 4),
                "total_steps": total_steps,
                "failed_steps": failed_steps,
                "step_error_rate": round(failed_steps / max(total_steps, 1), 4),
                "throughput_iterations_per_sec": round(total_iterations / max(run_duration, 1), 2),
            },
            "per_user_results": [r.to_dict() for r in self._user_results.values()],
            "per_step_stats": {name: s.to_dict() for name, s in step_stats.items()},
        }


class StepTimer:
    """
    Context manager for timing named steps within a scenario.
    
    Usage:
        async with step_timer.time("login_submit"):
            await page.click("#submit")
            await page.wait_for_url("/dashboard")
    """

    def __init__(
        self,
        collector: MetricsCollector,
        user_id: int,
        iteration: int,
    ) -> None:
        self.collector = collector
        self.user_id = user_id
        self.iteration = iteration
    
    @asynccontextmanager
    async def time(self, step_name: str) -> AsyncIterator[None]:
        """Time a named step."""
        start_time = time.time()
        error: str | None = None
        success = True
        
        try:
            yield
        except Exception as e:
            success = False
            error = f"{type(e).__name__}: {str(e)}"
            raise
        finally:
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            metric = StepMetric(
                user_id=self.user_id,
                iteration=self.iteration,
                step_name=step_name,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                success=success,
                error=error,
            )
            await self.collector.record_step(metric)
