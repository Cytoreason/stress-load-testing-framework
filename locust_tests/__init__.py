"""
Locust Load Testing Framework.

A comprehensive framework for performance and load testing
of the CytoReason platform.

Example usage:
    >>> from locust_tests import UIFlowUser, get_config
    >>> config = get_config()
    >>> print(f"Testing: {config.base_url}")
"""
from locust_tests.locustfiles import BaseTaskSet, UIFlowTaskSet, UIFlowUser
from locust_tests.utils import Config, DiseaseConfig, get_config, get_logger, load_config, setup_logger

__version__ = "1.0.0"
__all__ = [
    # Version
    "__version__",
    # Task sets
    "BaseTaskSet",
    "UIFlowTaskSet",
    "UIFlowUser",
    # Config
    "Config",
    "DiseaseConfig",
    "load_config",
    "get_config",
    # Logger
    "setup_logger",
    "get_logger",
]