"""
Pytest configuration and fixtures for load testing
"""
import pytest
import os
from pathlib import Path
from locust_tests.config.settings import config
from locust_tests.utils.logger import setup_logger

logger = setup_logger()


@pytest.fixture(scope="session")
def test_config():
    """Fixture to provide test configuration"""
    return config


@pytest.fixture(scope="session")
def base_url():
    """Fixture to provide base URL"""
    return config.base_url


@pytest.fixture(scope="session")
def report_dir():
    """Fixture to create and provide report directory"""
    report_path = Path(config.report_dir)
    report_path.mkdir(parents=True, exist_ok=True)
    return str(report_path)


@pytest.fixture(scope="function")
def locust_environment():
    """Fixture to provide a Locust environment for testing"""
    from locust import Environment
    from locust.stats import stats_printer, stats_history
    from locust.log import setup_logging
    import gevent

    setup_logging("INFO")

    env = Environment(
        user_classes=[],
        events=None,
        host=config.base_url
    )

    # Start background tasks
    gevent.spawn(stats_printer(env.stats))
    gevent.spawn(stats_history, env.runner)

    yield env

    # Cleanup
    if env.runner:
        env.runner.quit()


@pytest.fixture(scope="function")
def load_test_stats():
    """Fixture to track load test statistics"""
    stats = {
        "total_requests": 0,
        "failed_requests": 0,
        "success_rate": 0,
        "avg_response_time": 0,
        "max_response_time": 0,
        "requests_per_second": 0
    }
    return stats


def pytest_configure(config):
    """Pytest configuration hook"""
    logger.info("Initializing load test framework")


def pytest_sessionstart(session):
    """Called after the Session object has been created"""
    logger.info("Starting test session")


def pytest_sessionfinish(session, exitstatus):
    """Called after whole test run finished"""
    logger.info(f"Test session finished with status: {exitstatus}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to track test outcomes"""
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call":
        if rep.failed:
            logger.error(f"Test failed: {item.nodeid}")
        elif rep.passed:
            logger.info(f"Test passed: {item.nodeid}")
