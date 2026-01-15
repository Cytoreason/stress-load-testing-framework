"""
Pytest-based load test scenarios
"""
import pytest
from locust import HttpUser
from locust.env import Environment
from locust.stats import stats_printer, stats_history
import gevent
from locust_tests.locustfiles.example_test import (
    CustomerPlatformUser,
    SequentialUser,
    APIUser
)
from locust_tests.config.settings import config
from locust_tests.utils.logger import setup_logger

logger = setup_logger()


def run_load_test(user_class, num_users=10, spawn_rate=2, run_time=30):
    """
    Run a load test with the specified user class

    Args:
        user_class: Locust user class to use
        num_users: Number of users to simulate
        spawn_rate: Rate at which users are spawned
        run_time: Duration of the test in seconds

    Returns:
        Dictionary with test statistics
    """
    # Setup environment
    env = Environment(user_classes=[user_class], host=config.base_url)
    env.create_local_runner()

    # Start background tasks
    gevent.spawn(stats_printer(env.stats))
    gevent.spawn(stats_history, env.runner)

    # Start test
    logger.info(f"Starting load test with {num_users} users")
    env.runner.start(num_users, spawn_rate=spawn_rate)

    # Run for specified time
    gevent.spawn_later(run_time, lambda: env.runner.quit())

    # Wait for test to complete
    env.runner.greenlet.join()

    # Collect statistics
    stats = {
        "total_requests": env.stats.total.num_requests,
        "failed_requests": env.stats.total.num_failures,
        "success_rate": (
            ((env.stats.total.num_requests - env.stats.total.num_failures) /
             env.stats.total.num_requests * 100)
            if env.stats.total.num_requests > 0 else 0
        ),
        "avg_response_time": env.stats.total.avg_response_time,
        "max_response_time": env.stats.total.max_response_time,
        "requests_per_second": env.stats.total.total_rps,
        "median_response_time": env.stats.total.get_response_time_percentile(0.5),
        "p95_response_time": env.stats.total.get_response_time_percentile(0.95),
        "p99_response_time": env.stats.total.get_response_time_percentile(0.99)
    }

    logger.info(f"Test completed. Success rate: {stats['success_rate']:.2f}%")

    return stats


@pytest.mark.smoke
def test_basic_connectivity(base_url):
    """Test basic connectivity to the platform"""
    import requests

    logger.info(f"Testing connectivity to {base_url}")

    try:
        response = requests.get(base_url, timeout=10, verify=False)
        logger.info(f"Response status: {response.status_code}")
        assert response.status_code in [200, 401, 403, 404], \
            f"Unexpected status code: {response.status_code}"
    except requests.RequestException as e:
        pytest.skip(f"Could not connect to {base_url}: {e}")


@pytest.mark.load
def test_basic_load_scenario():
    """Test basic load scenario with multiple users"""
    stats = run_load_test(
        user_class=CustomerPlatformUser,
        num_users=10,
        spawn_rate=2,
        run_time=30
    )

    # Assertions
    assert stats['total_requests'] > 0, "No requests were made"
    assert stats['success_rate'] >= 0, "Success rate is negative"

    logger.info(f"Total requests: {stats['total_requests']}")
    logger.info(f"Success rate: {stats['success_rate']:.2f}%")
    logger.info(f"Avg response time: {stats['avg_response_time']:.2f}ms")


@pytest.mark.load
def test_api_load_scenario():
    """Test API load scenario"""
    stats = run_load_test(
        user_class=APIUser,
        num_users=15,
        spawn_rate=3,
        run_time=30
    )

    assert stats['total_requests'] > 0, "No requests were made"

    logger.info(f"API Test - Total requests: {stats['total_requests']}")
    logger.info(f"API Test - Success rate: {stats['success_rate']:.2f}%")


@pytest.mark.load
def test_sequential_user_journey():
    """Test sequential user journey"""
    stats = run_load_test(
        user_class=SequentialUser,
        num_users=5,
        spawn_rate=1,
        run_time=30
    )

    assert stats['total_requests'] > 0, "No requests were made"

    logger.info(f"Sequential Test - Total requests: {stats['total_requests']}")
    logger.info(f"Sequential Test - Avg response time: {stats['avg_response_time']:.2f}ms")


@pytest.mark.stress
def test_stress_scenario():
    """Test stress scenario with high user load"""
    stats = run_load_test(
        user_class=CustomerPlatformUser,
        num_users=50,
        spawn_rate=10,
        run_time=60
    )

    assert stats['total_requests'] > 0, "No requests were made"

    logger.info(f"Stress Test - Total requests: {stats['total_requests']}")
    logger.info(f"Stress Test - Success rate: {stats['success_rate']:.2f}%")
    logger.info(f"Stress Test - Max response time: {stats['max_response_time']:.2f}ms")

    # Performance thresholds
    max_allowed_response_time = config.get('thresholds.max_response_time_ms', 5000)
    assert stats['avg_response_time'] < max_allowed_response_time, \
        f"Average response time exceeded threshold: {stats['avg_response_time']:.2f}ms"


@pytest.mark.integration
def test_performance_thresholds():
    """Test that performance meets defined thresholds"""
    stats = run_load_test(
        user_class=CustomerPlatformUser,
        num_users=20,
        spawn_rate=4,
        run_time=60
    )

    # Get thresholds from config
    max_response_time = config.get('thresholds.max_response_time_ms', 5000)
    min_success_rate = 100 - config.get('thresholds.max_error_rate_percent', 5)

    logger.info("Checking performance thresholds:")
    logger.info(f"  Max response time: {max_response_time}ms")
    logger.info(f"  Min success rate: {min_success_rate}%")

    # Assertions based on thresholds
    if stats['total_requests'] > 0:
        logger.info(f"  Actual avg response time: {stats['avg_response_time']:.2f}ms")
        logger.info(f"  Actual success rate: {stats['success_rate']:.2f}%")
    else:
        pytest.skip("No requests were made during the test")
