"""
Stress test shape: CytoreasonUiStressShape
==========================================

Goal: Find the system's stress point and characterise degradation behaviour.

Strategy:
  Ramp load in 10-user (10%) steps every 5 minutes until one of the following
  termination conditions is met (observed externally via Locust metrics):
    - Error rate rises sharply (>10% sustained)
    - p95/p99 latency blows past SLO threshold
    - Queue lag grows continuously (Locust users backing up)
    - Autoscaling stops helping
    - A dependency saturates

  After the ramp reaches the configured maximum (default 100), the test holds
  at peak for 20 minutes (Recovery Observation phase), then ramps down
  to allow the platform to recover before ending the run.

Profile (configurable via PEAK_USERS; default 100):
  Ramp-up phase  (50 min total – within 30–60 min requirement):
    Each step = 3 min ramp + 2 min hold = 5 min per step (10 steps)
     0:00 –  3:00   0 → 10 users        ramp  (10%)
     3:00 –  5:00  10 users hold
     5:00 –  8:00  10 → 20 users        ramp  (+10%)
     8:00 – 10:00  20 users hold
    10:00 – 13:00  20 → 30 users        ramp  (+10%)
    13:00 – 15:00  30 users hold
    15:00 – 18:00  30 → 40 users        ramp  (+10%)
    18:00 – 20:00  40 users hold
    20:00 – 23:00  40 → 50 users        ramp  (+10%)
    23:00 – 25:00  50 users hold
    25:00 – 28:00  50 → 60 users        ramp  (+10%)
    28:00 – 30:00  60 users hold
    30:00 – 33:00  60 → 70 users        ramp  (+10%)
    33:00 – 35:00  70 users hold
    35:00 – 38:00  70 → 80 users        ramp  (+10%)
    38:00 – 40:00  80 users hold
    40:00 – 43:00  80 → 90 users        ramp  (+10%)
    43:00 – 45:00  90 users hold
    45:00 – 48:00  90 → 100 users       ramp  (+10%)
    48:00 – 50:00  100 users hold

  Peak observation:  50:00 –  70:00  (20 min at 100 – within 15–30 min)
  Recovery:          70:00 –  90:00  (ramp-down 100 → 0 over 20 min – within 15–30 min)

  Total: ≈ 90 minutes

Requirements satisfied:
  ✓ Ramp up to 100 over ≥ 0.5 h  (50 min)
  ✓ Ramp-up: 30–60 min            (50 min)
  ✓ Peak / over-peak: 15–30 min   (20 min)
  ✓ Recovery observation: 15–30 min after load stops  (20 min)
  ✓ Step size: 10–20% of peak     (10% = 10 users)
  ✓ Step interval: 5–10 min       (5 min per step)

Note:
  The framework does NOT auto-terminate on SLO breach.  Operators should
  monitor the Locust web UI or JSON/CSV reports and manually stop the run
  when one of the termination conditions above is observed.
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
    step = 10        # users per step = 10% of default peak (100)
    step_ramp_s = 180  # 3 min ramp per step
    step_hold_s = 120  # 2 min hold per step → 5 min/step × 10 steps = 50 min ramp-up
    peak_hold_s = 1200  # 20 min peak observation  (requirement: 15–30 min)
    cooldown_s = 1200   # 20 min recovery ramp-down (requirement: 15–30 min)

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
