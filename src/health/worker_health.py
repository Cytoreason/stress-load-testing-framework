"""
Worker / load-generator health monitor.

Validates that the machine generating the load is NOT itself the bottleneck.
Should be called at Locust init time (via ``init`` event) and periodically
during the run (via a background greenlet or the ``heartbeat`` mechanism).

Thresholds are intentionally conservative:
  - CPU  > 75% sustained  → warning; > 90% → critical
  - RAM  > 80% used       → warning; > 90% → critical
  - open file descriptors > 80% of limit → warning

If a critical threshold is breached, the health check emits an error-level
log that operators should treat as a signal to add more Locust workers or
reduce the users-per-worker ceiling.

Recommended browsers-per-worker:
  - Headless Chromium typically uses 200–400 MB RAM and 5–15% CPU per session.
  - A 4-core / 8 GB worker node can comfortably sustain 15–20 concurrent
    browser sessions without becoming a bottleneck.
  - For 100 concurrent users, provision at minimum 5–6 worker nodes.
"""
from __future__ import annotations

import logging
import os
import resource

import psutil

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ thresholds
_CPU_WARN_PCT = 75.0
_CPU_CRIT_PCT = 90.0
_MEM_WARN_PCT = 80.0
_MEM_CRIT_PCT = 90.0
_FD_WARN_RATIO = 0.80  # fraction of the OS fd limit


class WorkerHealthStatus:
    """Snapshot of the current worker health."""

    def __init__(
        self,
        cpu_pct: float,
        mem_pct: float,
        fd_pct: float,
        open_fds: int,
        fd_limit: int,
    ) -> None:
        self.cpu_pct = cpu_pct
        self.mem_pct = mem_pct
        self.fd_pct = fd_pct
        self.open_fds = open_fds
        self.fd_limit = fd_limit

    @property
    def is_healthy(self) -> bool:
        return (
            self.cpu_pct < _CPU_CRIT_PCT
            and self.mem_pct < _MEM_CRIT_PCT
            and self.fd_pct < _FD_WARN_RATIO
        )

    def log(self) -> None:
        level = logging.WARNING if not self.is_healthy else logging.DEBUG
        logger.log(
            level,
            "[worker-health] CPU=%.1f%%  MEM=%.1f%%  FD=%d/%d (%.0f%%)",
            self.cpu_pct,
            self.mem_pct,
            self.open_fds,
            self.fd_limit,
            self.fd_pct * 100,
        )
        if self.cpu_pct >= _CPU_CRIT_PCT:
            logger.critical(
                "[worker-health] CRITICAL: CPU %.1f%% exceeds %.0f%%. "
                "This worker IS the bottleneck. Add more Locust worker nodes.",
                self.cpu_pct,
                _CPU_CRIT_PCT,
            )
        if self.mem_pct >= _MEM_CRIT_PCT:
            logger.critical(
                "[worker-health] CRITICAL: RAM %.1f%% exceeds %.0f%%. "
                "Browser processes may be OOM-killed.",
                self.mem_pct,
                _MEM_CRIT_PCT,
            )


def check_worker_health() -> WorkerHealthStatus:
    """
    Collect current machine health metrics and return a status object.

    Safe to call from greenlets; psutil calls are non-blocking.
    """
    cpu_pct = psutil.cpu_percent(interval=0.2)
    mem = psutil.virtual_memory()
    mem_pct = mem.percent

    try:
        soft_limit, _ = resource.getrlimit(resource.RLIMIT_NOFILE)
        open_fds = len(os.listdir("/proc/self/fd"))
        fd_pct = open_fds / soft_limit if soft_limit > 0 else 0.0
    except (OSError, PermissionError):
        soft_limit = 0
        open_fds = 0
        fd_pct = 0.0

    status = WorkerHealthStatus(
        cpu_pct=cpu_pct,
        mem_pct=mem_pct,
        fd_pct=fd_pct,
        open_fds=open_fds,
        fd_limit=soft_limit,
    )
    status.log()
    return status


def assert_worker_healthy(*, raise_on_critical: bool = False) -> WorkerHealthStatus:
    """
    Check health and optionally raise if the worker is in a critical state.

    Called at Locust ``init`` event to abort before a run starts on an
    already-saturated machine.
    """
    status = check_worker_health()
    if not status.is_healthy and raise_on_critical:
        raise RuntimeError(
            f"Worker health check failed: CPU={status.cpu_pct:.1f}% "
            f"MEM={status.mem_pct:.1f}%. Refusing to start the run."
        )
    return status
