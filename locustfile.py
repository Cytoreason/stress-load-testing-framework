"""
Main Locust file for load testing
This is the entry point for running locust tests
"""
from locust_tests.config.settings import config
from locust_tests.locustfiles.example_test import (
    CustomerPlatformUser,
    SequentialUser,
    APIUser
)

# Set the host from configuration
# This will be used as the base URL for all requests
host = config.base_url

# Export user classes
__all__ = [
    'CustomerPlatformUser',
    'SequentialUser',
    'APIUser'
]
