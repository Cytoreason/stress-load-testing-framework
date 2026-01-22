"""
High Load Test Entry Point - 100 Concurrent Users.

This test simulates 100 concurrent users performing mixed workload
actions on the CytoReason platform.

Usage:
    # Web UI mode (recommended for monitoring):
    locust -f locustfile_high_load.py --host https://apps.private.cytoreason.com --web-port 8090

    # Headless mode with HTML report:
    locust -f locustfile_high_load.py --host https://apps.private.cytoreason.com \
           --headless --html reports/high_load_report.html

    # Quick test (override shape):
    locust -f locustfile_high_load.py --host https://apps.private.cytoreason.com \
           --headless -u 100 -r 10 --run-time 5m

Test Configuration:
    - Peak Users: 100 concurrent
    - Duration: 20 minutes total
    - Ramp Pattern: 20 → 50 → 100 → 50 → 0

Task Distribution (weighted):
    - Light tasks (browsing): 24 weight
    - Medium tasks (queries): 18 weight  
    - Heavy tasks (data): 9 weight
    - Special tasks (switch): 1 weight
"""
from locust_tests.locustfiles.high_load_test import (
    HighLoadTaskSet,
    HighLoadTestShape,
    HighLoadUser,
)

# Re-export for Locust discovery
__all__ = ["HighLoadUser", "HighLoadTestShape", "HighLoadTaskSet"]
