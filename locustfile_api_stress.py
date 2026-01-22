"""
API Stress Test Entry Point.

Direct API endpoint testing under concurrent load.
Run: locust -f locustfile_api_stress.py --host https://apps.private.cytoreason.com
"""
from locust_tests.locustfiles.api_stress_test import APIStressUser

__all__ = ["APIStressUser"]
