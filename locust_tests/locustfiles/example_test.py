"""
Example load test scenario for the Cytoreason platform
"""
from locust import task, between, SequentialTaskSet
from locust_tests.locustfiles.base_user import BaseLoadTestUser
from locust_tests.utils.helpers import wait_random, generate_random_data
from locust_tests.utils.logger import setup_logger

logger = setup_logger()


class CustomerPlatformUser(BaseLoadTestUser):
    """
    Simulated user for the Cytoreason customer platform
    """

    wait_time = between(2, 5)

    @task(3)
    def view_homepage(self):
        """View the platform homepage"""
        with self.client.get(
            "/",
            name="View Homepage",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                logger.debug("Homepage loaded successfully")
                response.success()
            else:
                logger.error(f"Homepage failed with status: {response.status_code}")
                response.failure(f"Failed with status code: {response.status_code}")

    @task(2)
    def view_dashboard(self):
        """View customer dashboard"""
        with self.client.get(
            "/dashboard",
            name="View Dashboard",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                # 404 is acceptable if dashboard endpoint doesn't exist
                response.success()
            else:
                response.failure(f"Dashboard failed with status: {response.status_code}")

    @task(1)
    def view_reports(self):
        """View reports section"""
        with self.client.get(
            "/reports",
            name="View Reports",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Reports failed with status: {response.status_code}")

    @task(1)
    def view_analytics(self):
        """View analytics section"""
        with self.client.get(
            "/analytics",
            name="View Analytics",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Analytics failed with status: {response.status_code}")


class SequentialUserJourney(SequentialTaskSet):
    """
    Sequential user journey simulating typical user flow
    """

    @task
    def step_1_login_page(self):
        """Step 1: Visit login page"""
        self.client.get("/", name="Step 1: Login Page")
        wait_random(1, 2)

    @task
    def step_2_dashboard(self):
        """Step 2: Navigate to dashboard"""
        self.client.get("/dashboard", name="Step 2: Dashboard")
        wait_random(2, 4)

    @task
    def step_3_view_data(self):
        """Step 3: View data section"""
        self.client.get("/data", name="Step 3: View Data")
        wait_random(1, 3)

    @task
    def step_4_reports(self):
        """Step 4: Access reports"""
        self.client.get("/reports", name="Step 4: Reports")
        wait_random(2, 3)

    @task
    def step_5_logout(self):
        """Step 5: Logout"""
        self.client.get("/logout", name="Step 5: Logout")


class SequentialUser(BaseLoadTestUser):
    """User that follows a sequential task flow"""

    tasks = [SequentialUserJourney]
    wait_time = between(1, 3)


class APIUser(BaseLoadTestUser):
    """
    User simulating API calls to the platform
    """

    wait_time = between(1, 2)

    @task(3)
    def get_customer_data(self):
        """Get customer data via API"""
        with self.client.get(
            "/api/customers",
            name="API: Get Customers",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404, 401]:
                # These are acceptable responses
                response.success()
            else:
                response.failure(f"API call failed: {response.status_code}")

    @task(2)
    def get_platform_status(self):
        """Get platform status"""
        with self.client.get(
            "/api/status",
            name="API: Platform Status",
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(f"Status check failed: {response.status_code}")

    @task(1)
    def post_analytics_event(self):
        """Post analytics event"""
        event_data = {
            "event_type": "page_view",
            "user_id": generate_random_data("string", length=10),
            "timestamp": generate_random_data("datetime"),
            "properties": {
                "page": "/dashboard",
                "duration": generate_random_data("integer", min=1, max=60)
            }
        }

        with self.client.post(
            "/api/analytics/events",
            json=event_data,
            name="API: Post Analytics Event",
            catch_response=True
        ) as response:
            if response.status_code in [200, 201, 404, 401]:
                response.success()
            else:
                response.failure(f"Analytics post failed: {response.status_code}")
