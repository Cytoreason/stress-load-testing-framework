"""
Example: Creating a custom user class for your application

This file demonstrates how to create custom load test scenarios
tailored to your specific application needs.
"""

from locust import task, between, SequentialTaskSet
from locust_tests.locustfiles.base_user import BaseLoadTestUser
from locust_tests.utils.helpers import generate_random_data, wait_random


# Example 1: Simple Custom User
class SimpleCustomUser(BaseLoadTestUser):
    """
    A simple custom user that performs basic operations
    """
    wait_time = between(1, 3)

    @task(3)
    def browse_homepage(self):
        """Most frequent task - browse homepage"""
        response = self.get("/")
        self.validate_response(response, expected_status=200)

    @task(2)
    def view_product(self):
        """View a product page"""
        product_id = generate_random_data("integer", min=1, max=100)
        response = self.get(f"/products/{product_id}")

    @task(1)
    def search(self):
        """Perform a search"""
        query = generate_random_data("string", length=10)
        response = self.get(f"/search?q={query}")


# Example 2: User with Authentication
class AuthenticatedUser(BaseLoadTestUser):
    """
    User that logs in before performing tasks
    """
    wait_time = between(2, 5)

    def on_start(self):
        """Login when user starts"""
        super().on_start()
        self.login()

    def login(self):
        """Perform login"""
        login_data = {
            "username": generate_random_data("email"),
            "password": "test_password"
        }
        response = self.post("/api/auth/login", json_data=login_data)

        if response.status_code == 200:
            # Store token for subsequent requests
            token = response.json().get("token")
            if token:
                self.auth_headers["Authorization"] = f"Bearer {token}"

    @task
    def view_dashboard(self):
        """Access authenticated dashboard"""
        self.get("/dashboard")

    @task
    def get_user_data(self):
        """Get user-specific data"""
        self.get("/api/user/profile")


# Example 3: E-commerce User Journey
class ShoppingJourney(SequentialTaskSet):
    """
    Sequential tasks representing a complete shopping journey
    """

    @task
    def step_1_browse_catalog(self):
        """Browse product catalog"""
        self.client.get("/products", name="1. Browse Catalog")
        wait_random(2, 4)

    @task
    def step_2_view_product(self):
        """View specific product"""
        product_id = generate_random_data("integer", min=1, max=50)
        self.client.get(f"/products/{product_id}", name="2. View Product")
        wait_random(3, 6)

    @task
    def step_3_add_to_cart(self):
        """Add product to cart"""
        cart_data = {
            "product_id": generate_random_data("integer", min=1, max=50),
            "quantity": generate_random_data("integer", min=1, max=3)
        }
        self.client.post("/api/cart/add", json=cart_data, name="3. Add to Cart")
        wait_random(1, 2)

    @task
    def step_4_view_cart(self):
        """View shopping cart"""
        self.client.get("/cart", name="4. View Cart")
        wait_random(2, 3)

    @task
    def step_5_checkout(self):
        """Proceed to checkout"""
        checkout_data = {
            "address": generate_random_data("address"),
            "payment_method": "credit_card"
        }
        self.client.post("/api/checkout", json=checkout_data, name="5. Checkout")


class EcommerceUser(BaseLoadTestUser):
    """User that follows the shopping journey"""
    tasks = [ShoppingJourney]
    wait_time = between(1, 3)


# Example 4: API-Heavy User
class APIHeavyUser(BaseLoadTestUser):
    """
    User that primarily interacts with APIs
    """
    wait_time = between(0.5, 2)

    @task(5)
    def get_data(self):
        """Frequent GET requests"""
        endpoints = ["/api/data", "/api/stats", "/api/info"]
        endpoint = generate_random_data("string")  # Would use random.choice in real scenario
        self.get(endpoints[0])

    @task(3)
    def post_data(self):
        """POST requests with data"""
        data = {
            "timestamp": generate_random_data("datetime"),
            "value": generate_random_data("float", min=0, max=100),
            "status": generate_random_data("boolean")
        }
        self.post("/api/data", json_data=data)

    @task(1)
    def update_data(self):
        """PUT requests to update data"""
        item_id = generate_random_data("integer", min=1, max=1000)
        data = {"status": "updated"}
        self.put(f"/api/data/{item_id}", json_data=data)


# Example 5: Custom Request Handler with Validation
class ValidatedUser(BaseLoadTestUser):
    """
    User that performs extensive response validation
    """
    wait_time = between(1, 2)

    @task
    def validated_request(self):
        """Request with comprehensive validation"""
        response = self.get("/api/users")

        # Validate status code
        if not self.validate_response(response, expected_status=200):
            return

        # Additional custom validation
        try:
            data = response.json()

            # Check response structure
            if not isinstance(data, list):
                self.environment.events.request.fire(
                    request_type="GET",
                    name="/api/users",
                    response_time=response.elapsed.total_seconds() * 1000,
                    response_length=len(response.content),
                    exception=Exception("Response is not a list"),
                )
                return

            # Check data quality
            if len(data) == 0:
                print("Warning: Empty response received")

        except Exception as e:
            print(f"Validation error: {e}")


# Example 6: Mixed Behavior User
class MixedBehaviorUser(BaseLoadTestUser):
    """
    User with different behavior patterns (80% read, 20% write)
    """
    wait_time = between(1, 3)

    @task(8)  # 80% of tasks
    def read_operations(self):
        """Read-heavy operations"""
        operations = [
            lambda: self.get("/"),
            lambda: self.get("/api/data"),
            lambda: self.get("/reports"),
        ]
        # In real scenario, use random.choice(operations)()
        self.get("/")

    @task(2)  # 20% of tasks
    def write_operations(self):
        """Write operations"""
        data = {
            "action": "create",
            "timestamp": generate_random_data("datetime")
        }
        self.post("/api/actions", json_data=data)


# Usage Instructions:
"""
To use these examples:

1. Copy the desired user class to your locustfile.py or a new file
2. Customize the endpoints and data to match your application
3. Run with Locust:
   locust -f examples/custom_user_example.py SimpleCustomUser

4. Or reference in your main locustfile.py:
   from examples.custom_user_example import SimpleCustomUser
"""
