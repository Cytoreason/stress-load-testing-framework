from __future__ import annotations

from dataclasses import dataclass

from locust import LoadTestShape


@dataclass(frozen=True)
class Segment:
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
        val = self.users_from + (self.users_to - self.users_from) * progress
        return int(round(val))


class CytoreasonUiShape(LoadTestShape):
    """
    Requested profile:
      - linear 0 -> 10 over 5m
      - keep 10 for 1m
      - linear 10 -> 50 over 10m
      - keep 50 for 10m
      - linear 50 -> 100 over 15m
      - keep 100 for 10m
      - ramp down 100 -> 0 over 5m

    Total: 56m = 3360s
    """

    segments = [
        Segment("warmup_ramp_0_10", 0, 300, 0, 10),
        Segment("hold_10", 300, 360, 10, 10),
        Segment("ramp_10_50", 360, 960, 10, 50),
        Segment("hold_50", 960, 1560, 50, 50),
        Segment("ramp_50_100", 1560, 2460, 50, 100),
        Segment("hold_100", 2460, 3060, 100, 100),
        Segment("rampdown_100_0", 3060, 3360, 100, 0),
    ]

    def tick(self):
        t = self.get_run_time()

        if t >= 3360:
            return None

        for seg in self.segments:
            if seg.contains(t):
                user_count = max(0, seg.target_users(t))
                # spawn_rate is a "how fast can we adjust" guardrail.
                spawn_rate = 5
                return (user_count, spawn_rate)

        return None
