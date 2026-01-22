"""
Data Query Test Entry Point.

Heavy data operations testing - large queries, complex filters.
Run: locust -f locustfile_data_query.py --host https://apps.private.cytoreason.com
"""
from locust_tests.locustfiles.data_query_test import DataQueryUser

__all__ = ["DataQueryUser"]
