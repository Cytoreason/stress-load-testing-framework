"""
Spike Test Entry Point.

Tests system resilience under sudden traffic spikes.
Run: locust -f locustfile_spike.py --host https://apps.private.cytoreason.com

Load Pattern:
    Baseline (5) → Spike (50) → Recovery → Spike (75) → Recovery → Max (100) → Cooldown
    Total: 7 minutes
"""
from locust_tests.locustfiles.spike_test import SpikeUser, SpikeTestShape

__all__ = ["SpikeUser", "SpikeTestShape"]
