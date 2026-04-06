"""
Shape profile unit tests.

Validates that LOAD and STRESS Locust shapes produce segment sequences that
conform to documented timing requirements — without starting Locust or a
browser.

Requirements asserted:

  STRESS shape
  ────────────
  • Ramp-up total:            30–60 min
  • Per-step interval:         5–10 min  (ramp + hold combined)
  • Step size:                10–20% of peak users
  • Peak observation hold:    15–30 min
  • Recovery / cooldown:      15–30 min
  • Shape reaches PEAK users and ends at 0

  LOAD shape
  ──────────
  • Warm-up ramp (0 → 25%):  10–15 min
  • Hold at 25% / 50% / 75%: ≥ 10 min each
  • Steady state at 100%:    30–60 min
  • Over-peak at 125%:       10–15 min
  • Cool-down:                5–10 min
  • Step ramp pattern present: 25 → 50 → 75 → 100 → 125 % levels
  • Shape ends at 0 users
"""
from __future__ import annotations

import pytest

from perf.shape_load import _build_load_segments
from perf.shape_stress import _build_stress_segments

PEAK = 100  # canonical peak for all assertions


# ============================================================
# Stress shape
# ============================================================

class TestStressShape:

    @pytest.fixture(scope="class")
    def segs(self):
        return _build_stress_segments(PEAK)

    # ----------------------------------------------------------
    def test_ramp_up_duration_30_to_60_min(self, segs):
        """All step-ramp + step-hold segments before peak observation = 30–60 min."""
        ramp_segs = [
            s for s in segs
            if s.name.startswith("stress_ramp_") or s.name.startswith("stress_hold_")
        ]
        assert ramp_segs, "No ramp/hold segments found"
        total_s = sum(s.end_s - s.start_s for s in ramp_segs)
        assert 1800 <= total_s <= 3600, (
            f"Stress ramp-up = {total_s}s ({total_s / 60:.0f} min); "
            "requirement: 30–60 min"
        )

    def test_each_step_interval_5_to_10_min(self, segs):
        """Ramp + hold pair for each step must total 5–10 min."""
        ramp_segs = [s for s in segs if s.name.startswith("stress_ramp_")]
        hold_segs = [s for s in segs if s.name.startswith("stress_hold_")]
        assert len(ramp_segs) == len(hold_segs), (
            "Mismatch: ramp segment count != hold segment count"
        )
        for ramp, hold in zip(ramp_segs, hold_segs):
            step_s = (ramp.end_s - ramp.start_s) + (hold.end_s - hold.start_s)
            assert 300 <= step_s <= 600, (
                f"Step {ramp.name}: {step_s}s ({step_s / 60:.1f} min); "
                "requirement: 5–10 min"
            )

    def test_step_size_10_to_20_pct_of_peak(self, segs):
        """Each ramp step must increment users by 10–20% of peak."""
        ramp_segs = [s for s in segs if s.name.startswith("stress_ramp_")]
        assert ramp_segs
        for seg in ramp_segs:
            increment = seg.users_to - seg.users_from
            pct = increment / PEAK * 100
            assert 10 <= pct <= 20, (
                f"{seg.name}: increment={increment} users ({pct:.0f}% of peak); "
                "requirement: 10–20%"
            )

    def test_peak_observation_15_to_30_min(self, segs):
        """Peak observation hold must be 15–30 min."""
        obs = [s for s in segs if "peak_observation" in s.name]
        assert obs, "stress_peak_observation segment not found"
        dur_s = obs[0].end_s - obs[0].start_s
        assert 900 <= dur_s <= 1800, (
            f"Peak observation = {dur_s}s ({dur_s / 60:.0f} min); "
            "requirement: 15–30 min"
        )

    def test_cooldown_15_to_30_min(self, segs):
        """Recovery ramp-down must be 15–30 min."""
        cd = [s for s in segs if "cooldown" in s.name]
        assert cd, "stress_cooldown segment not found"
        dur_s = cd[0].end_s - cd[0].start_s
        assert 900 <= dur_s <= 1800, (
            f"Cooldown = {dur_s}s ({dur_s / 60:.0f} min); "
            "requirement: 15–30 min"
        )

    def test_reaches_peak_users(self, segs):
        """Shape must ramp all the way to PEAK_USERS."""
        assert max(s.users_to for s in segs) == PEAK

    def test_ends_at_zero_users(self, segs):
        """Shape must ramp down to 0 at the end of the cooldown."""
        cooldown = [s for s in segs if "cooldown" in s.name]
        assert cooldown, "cooldown segment not found"
        assert cooldown[-1].users_to == 0


# ============================================================
# Load shape
# ============================================================

class TestLoadShape:

    @pytest.fixture(scope="class")
    def segs(self):
        return _build_load_segments(PEAK)

    # ----------------------------------------------------------
    def test_warmup_10_to_15_min(self, segs):
        """Warm-up ramp (0 → 25%) must be 10–15 min."""
        warmup = [s for s in segs if "warmup" in s.name]
        assert warmup, "warmup segment not found"
        dur_s = warmup[0].end_s - warmup[0].start_s
        assert 600 <= dur_s <= 900, (
            f"Warmup = {dur_s}s ({dur_s / 60:.0f} min); requirement: 10–15 min"
        )

    @pytest.mark.parametrize("pct,label", [
        (25, "pct25"),
        (50, "pct50"),
        (75, "pct75"),
    ])
    def test_step_hold_at_level_ge_10_min(self, segs, pct, label):
        """Each step hold (25% / 50% / 75%) must be ≥ 10 min at the correct user count."""
        holds = [s for s in segs if f"hold_{label}" in s.name]
        assert holds, f"hold_{label} segment not found"
        expected_users = round(PEAK * pct / 100)
        for seg in holds:
            assert seg.users_from == expected_users == seg.users_to, (
                f"hold_{label}: users={seg.users_from}; expected {expected_users}"
            )
            dur_s = seg.end_s - seg.start_s
            assert dur_s >= 600, (
                f"hold_{label}: {dur_s}s ({dur_s / 60:.0f} min); requirement: ≥ 10 min"
            )

    def test_steady_state_100_pct_is_30_to_60_min(self, segs):
        """Steady state at 100% must be 30–60 min."""
        steady = [s for s in segs if "steady_100" in s.name]
        assert steady, "steady_100 segment not found"
        dur_s = steady[0].end_s - steady[0].start_s
        assert 1800 <= dur_s <= 3600, (
            f"Steady state = {dur_s}s ({dur_s / 60:.0f} min); requirement: 30–60 min"
        )
        assert steady[0].users_from == PEAK == steady[0].users_to

    def test_overpeak_125_pct_is_10_to_15_min(self, segs):
        """Over-peak at 125% must be 10–15 min."""
        op = [s for s in segs if "overpeak" in s.name]
        assert op, "overpeak segment not found"
        dur_s = op[0].end_s - op[0].start_s
        assert 600 <= dur_s <= 900, (
            f"Over-peak = {dur_s}s ({dur_s / 60:.0f} min); requirement: 10–15 min"
        )
        assert op[0].users_from == round(PEAK * 1.25)

    def test_cooldown_5_to_10_min(self, segs):
        """Cool-down must be 5–10 min."""
        cd = [s for s in segs if "cooldown" in s.name]
        assert cd, "cooldown segment not found"
        dur_s = cd[0].end_s - cd[0].start_s
        assert 300 <= dur_s <= 600, (
            f"Cooldown = {dur_s}s ({dur_s / 60:.0f} min); requirement: 5–10 min"
        )

    def test_ends_at_zero_users(self, segs):
        """Load shape must ramp down to 0 at end of cool-down."""
        cd = [s for s in segs if "cooldown" in s.name]
        assert cd, "cooldown segment not found"
        assert cd[-1].users_to == 0

    def test_step_ramp_levels_present(self, segs):
        """Step-ramp pattern must include 25 / 50 / 75 / 100 / 125 % user levels."""
        all_user_levels = {s.users_to for s in segs} | {s.users_from for s in segs}
        expected = {
            round(PEAK * 0.25),
            round(PEAK * 0.50),
            round(PEAK * 0.75),
            PEAK,
            round(PEAK * 1.25),
        }
        for level in expected:
            assert level in all_user_levels, (
                f"Expected user level {level} ({level / PEAK * 100:.0f}%) "
                "not found in load shape"
            )
