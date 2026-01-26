"""
Hybrid Load Testing Framework - CytoReason Platform

Staged Load Test Pattern:
    Stage 1: Linear   0 →  10 over  5 min (warm up)
    Stage 2: Hold at  10 for  1 min
    Stage 3: Linear  10 →  50 over 10 min
    Stage 4: Hold at  50 for 10 min
    Stage 5: Linear  50 → 100 over 15 min
    Stage 6: Hold at 100 for 10 min
    Stage 7: Linear 100 →   0 over  5 min (ramp down)
    
    Total Duration: 56 minutes

Target URLs:
    - UI:  https://apps.private.cytoreason.com/platform/customers/pyy/
    - API: https://api.platform.private.cytoreason.com/v1.0/customer/pyy/e2/platform

Usage:
    # Run staged load test (uses custom shape automatically)
    locust -f locustfile.py
    
    # Then click START in web UI (users/spawn rate ignored - shape controls it)

Credentials:
    Set via environment variables:
    - DEFAULT_USERNAME
    - DEFAULT_PASSWORD
"""

from locust import HttpUser, task, constant, LoadTestShape

from scenarios.ui_user import UIStressUser
from scenarios.api_user import BackendStresser


class StagedLoadShape(LoadTestShape):
    """
    Custom load shape for staged ramp-up/ramp-down testing.
    
    Pattern:
        0 →  10 over  5 min (warm up)
        Hold 10 for  1 min
        10 →  50 over 10 min
        Hold 50 for 10 min
        50 → 100 over 15 min
        Hold 100 for 10 min
        100 →  0 over  5 min (ramp down)
    
    Total: 56 minutes
    """
    
    # Define stages: (duration_seconds, start_users, end_users, spawn_rate)
    # spawn_rate is users per second for ramping
    stages = [
        # Stage 1: Warm up 0 → 10 over 5 minutes
        {"duration": 5 * 60, "start_users": 0, "end_users": 10, "name": "Warm Up"},
        # Stage 2: Hold at 10 for 1 minute
        {"duration": 1 * 60, "start_users": 10, "end_users": 10, "name": "Hold 10"},
        # Stage 3: Ramp 10 → 50 over 10 minutes
        {"duration": 10 * 60, "start_users": 10, "end_users": 50, "name": "Ramp to 50"},
        # Stage 4: Hold at 50 for 10 minutes
        {"duration": 10 * 60, "start_users": 50, "end_users": 50, "name": "Hold 50"},
        # Stage 5: Ramp 50 → 100 over 15 minutes
        {"duration": 15 * 60, "start_users": 50, "end_users": 100, "name": "Ramp to 100"},
        # Stage 6: Hold at 100 for 10 minutes
        {"duration": 10 * 60, "start_users": 100, "end_users": 100, "name": "Hold 100"},
        # Stage 7: Ramp down 100 → 0 over 5 minutes
        {"duration": 5 * 60, "start_users": 100, "end_users": 0, "name": "Ramp Down"},
    ]
    
    def tick(self):
        """
        Called by Locust to determine current user count and spawn rate.
        
        Returns:
            tuple: (user_count, spawn_rate) or None to stop the test
        """
        run_time = self.get_run_time()
        
        # Calculate cumulative time for each stage
        cumulative_time = 0
        for stage in self.stages:
            stage_start = cumulative_time
            stage_end = cumulative_time + stage["duration"]
            
            if stage_start <= run_time < stage_end:
                # We're in this stage
                time_in_stage = run_time - stage_start
                stage_progress = time_in_stage / stage["duration"]
                
                # Linear interpolation between start and end users
                start_users = stage["start_users"]
                end_users = stage["end_users"]
                target_users = int(start_users + (end_users - start_users) * stage_progress)
                
                # Ensure at least 1 user during test (except at very start/end)
                if target_users == 0 and run_time > 10:
                    target_users = 1
                
                # Calculate spawn rate based on how fast we need to change
                if end_users != start_users:
                    # Ramp stage: calculate required spawn rate
                    users_to_change = abs(end_users - start_users)
                    spawn_rate = max(1, users_to_change / stage["duration"])
                else:
                    # Hold stage: minimal spawn rate
                    spawn_rate = 1
                
                return (target_users, spawn_rate)
            
            cumulative_time = stage_end
        
        # Test complete
        return None


class APIStresser(BackendStresser):
    """
    API stress user for CytoReason backend load.
    
    Targets: https://api.platform.private.cytoreason.com
    """
    host = "https://api.platform.private.cytoreason.com"
    weight = 1  # Balanced with browser users
    wait_time = constant(1)


class BrowserUser(UIStressUser):
    """
    Browser-based user for CytoReason UI load testing.
    
    Uses Playwright to measure real client-side performance.
    
    Targets: https://apps.private.cytoreason.com/platform/customers/pyy/
    
    NOTE: At peak (100 users), with 5:1 browser:API ratio:
    ~83 browser users (~25GB RAM) + ~17 API users
    """
    host = "https://apps.private.cytoreason.com"
    weight = 5  # 5 browser users per 1 API user
    wait_time = constant(5)


# Export all classes
__all__ = ["StagedLoadShape", "APIStresser", "BrowserUser", "BackendStresser", "UIStressUser"]
