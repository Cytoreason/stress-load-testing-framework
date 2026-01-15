"""
Base user class for Locust load testing
"""
from locust import HttpUser, task, between, events
from typing import Dict, Any, Optional
import json
from locust_tests.config.settings import config
from locust_tests.utils.auth import get_auth_headers
from locust_tests.utils.logger import setup_logger

logger = setup_logger()


class BaseLoadTestUser(HttpUser):
    """
    Base user class for load testing with common functionality
    """

    # Wait time between tasks (in seconds)
    wait_time = between(1, 3)

    # Set to False to not verify SSL certificates
    verify_ssl = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth_headers = {}
        self.default_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "LoadTestFramework/1.0"
        }

    def on_start(self):
        """
        Called when a simulated user starts before any tasks are executed
        Override this method for user-specific initialization
        """
        logger.info(f"User {id(self)} started")
        self._setup_authentication()

    def on_stop(self):
        """
        Called when a simulated user stops
        Override this method for cleanup
        """
        logger.info(f"User {id(self)} stopped")

    def _setup_authentication(self):
        """Setup authentication headers"""
        auth_type = config.get('auth.type', 'none')

        if auth_type == 'token':
            token = config.get('auth.token')
            if token:
                self.auth_headers = get_auth_headers(auth_type='token', token=token)

        elif auth_type == 'basic':
            username = config.get('auth.username')
            password = config.get('auth.password')
            if username and password:
                self.auth_headers = get_auth_headers(
                    auth_type='basic',
                    username=username,
                    password=password
                )

        elif auth_type == 'api_key':
            api_key = config.get('auth.api_key')
            if api_key:
                self.auth_headers = get_auth_headers(auth_type='api_key', api_key=api_key)

        logger.debug(f"Authentication setup complete: {auth_type}")

    def _get_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Merge default headers, auth headers, and additional headers

        Args:
            additional_headers: Additional headers to include

        Returns:
            Combined headers dictionary
        """
        headers = {**self.default_headers}
        headers.update(self.auth_headers)

        if additional_headers:
            headers.update(additional_headers)

        return headers

    def get(
        self,
        path: str,
        name: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """
        Perform GET request with default headers and authentication

        Args:
            path: API endpoint path
            name: Optional name for the request in reports
            headers: Additional headers
            **kwargs: Additional arguments for requests

        Returns:
            Response object
        """
        return self.client.get(
            path,
            name=name or path,
            headers=self._get_headers(headers),
            **kwargs
        )

    def post(
        self,
        path: str,
        data: Optional[Any] = None,
        json_data: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """
        Perform POST request with default headers and authentication

        Args:
            path: API endpoint path
            data: Form data to send
            json_data: JSON data to send
            name: Optional name for the request in reports
            headers: Additional headers
            **kwargs: Additional arguments for requests

        Returns:
            Response object
        """
        if json_data is not None:
            kwargs['json'] = json_data
        elif data is not None:
            kwargs['data'] = data

        return self.client.post(
            path,
            name=name or path,
            headers=self._get_headers(headers),
            **kwargs
        )

    def put(
        self,
        path: str,
        data: Optional[Any] = None,
        json_data: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """
        Perform PUT request with default headers and authentication

        Args:
            path: API endpoint path
            data: Form data to send
            json_data: JSON data to send
            name: Optional name for the request in reports
            headers: Additional headers
            **kwargs: Additional arguments for requests

        Returns:
            Response object
        """
        if json_data is not None:
            kwargs['json'] = json_data
        elif data is not None:
            kwargs['data'] = data

        return self.client.put(
            path,
            name=name or path,
            headers=self._get_headers(headers),
            **kwargs
        )

    def delete(
        self,
        path: str,
        name: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """
        Perform DELETE request with default headers and authentication

        Args:
            path: API endpoint path
            name: Optional name for the request in reports
            headers: Additional headers
            **kwargs: Additional arguments for requests

        Returns:
            Response object
        """
        return self.client.delete(
            path,
            name=name or path,
            headers=self._get_headers(headers),
            **kwargs
        )

    def validate_response(
        self,
        response,
        expected_status: int = 200,
        expected_keys: Optional[list] = None
    ) -> bool:
        """
        Validate response status and optionally check for expected keys

        Args:
            response: Response object
            expected_status: Expected HTTP status code
            expected_keys: List of expected keys in JSON response

        Returns:
            True if validation passed, False otherwise
        """
        if response.status_code != expected_status:
            logger.error(
                f"Unexpected status code: {response.status_code}, "
                f"expected: {expected_status}"
            )
            return False

        if expected_keys:
            try:
                json_response = response.json()
                missing_keys = [key for key in expected_keys if key not in json_response]
                if missing_keys:
                    logger.error(f"Missing expected keys in response: {missing_keys}")
                    return False
            except json.JSONDecodeError:
                logger.error("Failed to decode JSON response")
                return False

        return True
