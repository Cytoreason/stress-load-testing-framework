"""
Stress test shape: CytoreasonUiStressShape
==========================================

Goal: Find the system's stress point and characterise degradation behaviour.

Strategy:
  Ramp load in 10-user steps every 5 minutes until one of the following
  termination conditions is met (observed externally via Locust metrics):
    - Error rate rises sharply (>10% sustained)
    - p95 latency exceeds SLO threshold (typically 15–20 s for a heavy
      Playwright-driven page load)
    - Queue lag grows continuously (Locust users backing up)
    - Autoscaling stops helping
    - A dependency saturates

  After the ramp reaches the configured maximum (default 100), the test holds
  at peak for 15–30 minutes (Recovery Observation phase), then ramps down
  to allow the platform to recover before ending the run.

Profile (configurable via PEAK_USERS; default 100):
  Ramp-up phase:
    0:00 –  5:00   0 → 10 users        (initial probe)
    5:00 – 10:00  10 users hold
   10:00 – 15:00  10 → 20 users
   15:00 – 20:00  20 users hold
   20:00 – 25:00  20 → 30 users
   25:00 – 30:00  30 users hold
   30:00 – 35:00  30 → 40 users
   35:00 – 40:00  40 users hold
   40:00 – 45:00  40 → 50 users
   45:00 – 50:00  50 users hold
   50:00 – 55:00  50 → 60 users
   55:00 – 60:00  60 users hold
   60:00 – 65:00  60 → 70 users
   65:00 – 70:00  70 users hold
   70:00 – 75:00  70 → 80 users
   75:00 – 80:00  80 users hold
   80:00 – 85:00  80 → 90 users
   85:00 – 90:00  90 users hold
   90:00 – 95:00  90 → 100 users

  Peak observation:  95:00 – 125:00  (30 min at 100)
  Recovery:         125:00 – 145:00  (ramp-down 100 → 0 over 20 min)

  Total: ≈ 145 minutes

Each step in the ramp-up represents a 10% increment, meeting the requirement
of "10–20% steps every 5–10 minutes".

Note:
  The framework does NOT auto-terminate on SLO breach (Locust does not have
  a built-in SLO hook).  Operators should monitor the Locust web UI or the
  JSON/CSV reports and manually stop the run when degradation is observed.
  A future enhancement could add a ``request`` event listener that sets an
  environment variable / flag to halt the shape early.
"""
from __future__ import annotations

from dataclasses import dataclass

from locust import LoadTestShape

from src.config import settings

_MAX_SPAWN_RATE: int = 2  # conservative for real browsers


@dataclass(frozen=True)
class _Segment:
    name: str
    start_s: int
    end_s: int
    users_from: int
    users_to: int

    def contains(self, t: float) -> bool:
        return self.start_s <= t < self.end_s

    def target_users(self, t: float) -> int:
        if self.users_from == self.users_to:
            return self.users_from
        progress = (t - self.start_s) / (self.end_s - self.start_s)
        return int(round(self.users_from + (self.users_to - self.users_from) * progress))


def _build_stress_segments(peak: int) -> list[_Segment]:
    """
    Build stress ramp segments: 10-user steps every 5 min hold.

    Each step is 10 min: 5 min ramp + 5 min hold.
    """
    step = 10  # users per step
    step_ramp_s = 300  # 5 min ramp
    step_hold_s = 300  # 5 min hold
    peak_hold_s = 1800  # 30 min peak observation
    cooldown_s = 1200  # 20 min ramp-down

    segments: list[_Segment] = []
    t = 0
    prev = 0

    while prev < peak:
        nxt = min(prev + step, peak)
        ramp_name = f"stress_ramp_{prev}_to_{nxt}_users"
        hold_name = f"stress_hold_{nxt}_users"
        segments.append(_Segment(ramp_name, t, t + step_ramp_s, prev, nxt))
        t += step_ramp_s
        segments.append(_Segment(hold_name, t, t + step_hold_s, nxt, nxt))
        t += step_hold_s
        prev = nxt

    segments.append(_Segment("stress_peak_observation", t, t + peak_hold_s, peak, peak))
    t += peak_hold_s
    segments.append(_Segment("stress_cooldown", t, t + cooldown_s, peak, 0))
    t += cooldown_s

    return segments


class CytoreasonUiStressShape(LoadTestShape):
    """
    10-user step ramp stress test shape for the CytoReason UI.

    Activated when TEST_PROFILE=stress.
    """

    def __init__(self) -> None:
        super().__init__()
        self._segments = _build_stress_segments(settings.peak_users)
        self._total_duration_s = self._segments[-1].end_s

    def tick(self) -> tuple[int, int] | None:
        t = self.get_run_time()

        if t >= self._total_duration_s:
            return None

        for seg in self._segments:
            if seg.contains(t):
                return (max(0, seg.target_users(t)), _MAX_SPAWN_RATE)

        return None
