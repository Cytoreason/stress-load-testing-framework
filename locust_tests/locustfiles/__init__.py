"""
Locust test files module.

Contains load test implementations for various scenarios.
"""
from locust_tests.locustfiles.base import BaseTaskSet
from locust_tests.locustfiles.ui_flow_test import UIFlowTaskSet, UIFlowUser
from locust_tests.locustfiles.api_stress_test import APIStressTaskSet, APIStressUser
from locust_tests.locustfiles.spike_test import SpikeTaskSet, SpikeUser, SpikeTestShape
from locust_tests.locustfiles.data_query_test import DataQueryTaskSet, DataQueryUser

__all__ = [
    # Base
    "BaseTaskSet",
    # UI Flow
    "UIFlowTaskSet",
    "UIFlowUser",
    # API Stress
    "APIStressTaskSet",
    "APIStressUser",
    # Spike
    "SpikeTaskSet",
    "SpikeUser",
    "SpikeTestShape",
    # Data Query
    "DataQueryTaskSet",
    "DataQueryUser",
]
