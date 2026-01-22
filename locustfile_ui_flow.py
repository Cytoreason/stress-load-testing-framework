"""
UI Flow Load Test Entry Point.

This is the main entry point for running UI flow load tests.
Run with: locust -f locustfile_ui_flow.py --host https://apps.private.cytoreason.com

The test uses a custom LoadTestShape that gradually ramps up users
to simulate realistic platform load patterns.
"""
from typing import Optional

from locust import LoadTestShape

from locust_tests.locustfiles.ui_flow_test import UIFlowUser

__all__ = ["UIFlowUser", "UIFlowTestShape"]


class UIFlowTestShape(LoadTestShape):
    """
    Custom load shape for UI flow testing.

    Designed for sequential user journey tests with gentle ramp-up,
    since each user performs a complete flow through the platform.

    Load Pattern:
        0 → 5 users    over 2 min   (warm up)
        Hold at 5      for 5 min    (baseline)
        5 → 20 users   over 5 min   (ramp up)
        Hold at 20     for 10 min   (sustained load)
        20 → 50 users  over 10 min  (stress)
        Hold at 50     for 15 min   (peak load)
        50 → 0 users   over 3 min   (ramp down)

        Total duration: ~50 minutes

    Attributes:
        stages: List of stage configurations with duration, users, and spawn_rate
    """

    # Stage configuration: each stage defines cumulative duration, target users, and spawn rate
    stages: list[dict[str, int]] = [
        {"duration": 120, "users": 5, "spawn_rate": 1},     # 0-2 min: warm up
        {"duration": 420, "users": 5, "spawn_rate": 1},     # 2-7 min: hold at 5
        {"duration": 720, "users": 20, "spawn_rate": 1},    # 7-12 min: ramp to 20
        {"duration": 1320, "users": 20, "spawn_rate": 1},   # 12-22 min: hold at 20
        {"duration": 1920, "users": 50, "spawn_rate": 1},   # 22-32 min: ramp to 50
        {"duration": 2820, "users": 50, "spawn_rate": 1},   # 32-47 min: hold at 50
        {"duration": 3000, "users": 0, "spawn_rate": 2},    # 47-50 min: ramp down
    ]

    def tick(self) -> Optional[tuple[int, float]]:
        """
        Calculate current user count based on elapsed time.

        Called by Locust to determine how many users should be active.
        Implements smooth ramping between stages.

        Returns:
            Tuple of (user_count, spawn_rate) or None to stop the test
        """
        run_time = self.get_run_time()

        for i, stage in enumerate(self.stages):
            if run_time < stage["duration"]:
                return self._calculate_users_for_stage(i, run_time)

        # Test complete - return None to stop
        return None

    def _calculate_users_for_stage(
        self, stage_index: int, run_time: float
    ) -> tuple[int, float]:
        """
        Calculate user count for a specific stage with ramping support.

        Args:
            stage_index: Index of the current stage
            run_time: Total elapsed time in seconds

        Returns:
            Tuple of (user_count, spawn_rate)
        """
        stage = self.stages[stage_index]

        if stage_index == 0:
            # First stage: linear ramp from 0 to target
            progress = run_time / stage["duration"]
            users = int(stage["users"] * progress)
            return (users, stage["spawn_rate"])

        prev_stage = self.stages[stage_index - 1]
        prev_users = prev_stage["users"]
        target_users = stage["users"]

        if prev_users == target_users:
            # Hold stage: maintain constant user count
            return (stage["users"], stage["spawn_rate"])

        # Ramping stage: linear interpolation between prev and target
        stage_start = prev_stage["duration"]
        stage_duration = stage["duration"] - stage_start
        stage_progress = (run_time - stage_start) / stage_duration

        current_users = int(prev_users + (target_users - prev_users) * stage_progress)
        return (max(0, current_users), stage["spawn_rate"])
