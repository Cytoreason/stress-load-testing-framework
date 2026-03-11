"""
Load test shape: CytoreasonUiLoadShape
=======================================

Goal: Measure stability and performance under expected UI load.

Profile (configurable via PEAK_USERS env var, default 100):
  - Warm-up:      10 min ramp 0 → 25% peak
  - Step 1:       10 min hold at 25% peak
  - Step 2:       10 min ramp 25% → 50% peak
  - Step 3:       10 min hold at 50% peak
  - Step 4:       10 min ramp 50% → 75% peak
  - Step 5:       10 min hold at 75% peak
  - Steady state: 30 min at 100% peak
  - Over-peak:    10–15 min at 125% peak
  - Cool-down:     5–10 min ramp 125% → 0

Total test duration: ~105–120 minutes

This profile deliberately uses step ramps (not a single jump) to distinguish
between ramp-induced latency artefacts and genuine steady-state degradation.

All parameters are derived from PEAK_USERS so the same shape scales with
different peak_user targets without code changes.

Spawn rate: 1 user/second (conservative – real browsers take ~2 s to launch).
Adjust MAX_SPAWN_RATE up to ~3 for faster ramp-ups if machines are oversized.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from locust import LoadTestShape

from src.config import settings

# Controls how fast Locust can add/remove users.  Keep ≤ 3 for headless
# browser users to avoid overwhelming the OS with concurrent browser starts.
_MAX_SPAWN_RATE: int = 3


@dataclass(frozen=True)
class _Segment:
    """A single time segment within the load profile."""

    name: str
    start_s: int    # seconds from test start
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


def _build_load_segments(peak: int) -> list[_Segment]:
    """
    Build the segment list for the given peak user count.

    All time values are in seconds.  Duration per phase:
      0:00 –  10:00  warm-up ramp      0 → 25%
     10:00 –  20:00  hold              25%
     20:00 –  30:00  ramp              25% → 50%
     30:00 –  40:00  hold              50%
     40:00 –  50:00  ramp              50% → 75%
     50:00 –  60:00  hold              75%
     60:00 –  90:00  steady state      100%
     90:00 – 105:00  over-peak         125%
    105:00 – 115:00  cool-down         100% → 0
    """
    p25 = max(1, round(peak * 0.25))
    p50 = max(1, round(peak * 0.50))
    p75 = max(1, round(peak * 0.75))
    p100 = peak
    p125 = max(1, round(peak * 1.25))

    return [
        _Segment("load_warmup_0_pct25",    0,      600,   0,    p25),
        _Segment("load_hold_pct25",       600,    1200,  p25,   p25),
        _Segment("load_ramp_pct25_pct50", 1200,   1800,  p25,   p50),
        _Segment("load_hold_pct50",       1800,   2400,  p50,   p50),
        _Segment("load_ramp_pct50_pct75", 2400,   3000,  p50,   p75),
        _Segment("load_hold_pct75",       3000,   3600,  p75,   p75),
        _Segment("load_steady_100_pct",   3600,   5400,  p100,  p100),
        _Segment("load_overpeak_125_pct", 5400,   6300,  p125,  p125),
        _Segment("load_cooldown",         6300,   6900,  p125,  0),
    ]


class CytoreasonUiLoadShape(LoadTestShape):
    """
    Step-ramp load test shape for the CytoReason UI.

    Activated when TEST_PROFILE=load (default).
    """

    def __init__(self) -> None:
        super().__init__()
        self._segments = _build_load_segments(settings.peak_users)
        self._total_duration_s = self._segments[-1].end_s

    def tick(self) -> tuple[int, int] | None:
        t = self.get_run_time()

        if t >= self._total_duration_s:
            return None  # Signal Locust to stop

        for seg in self._segments:
            if seg.contains(t):
                user_count = max(0, seg.target_users(t))
                return (user_count, _MAX_SPAWN_RATE)

        return None
