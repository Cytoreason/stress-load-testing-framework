"""
Base classes for Locust load tests.

Provides common functionality for all test task sets.
"""
import random
import time
from typing import Any, Optional

from locust import SequentialTaskSet
from locust.clients import ResponseContextManager

from locust_tests.utils.config_loader import Config, get_config
from locust_tests.utils.logger import get_logger

__all__ = ["BaseTaskSet"]


class BaseTaskSet(SequentialTaskSet):
    """
    Base class for all load test task sets.

    Provides common functionality:
    - Configuration loading
    - Authentication header management
    - Response validation
    - Payload building
    - Think time simulation
    """

    # Class-level configuration (loaded once)
    _config: Optional[Config] = None

    def __init__(self, parent: Any) -> None:
        """Initialize the task set with configuration."""
        super().__init__(parent)
        self.logger = get_logger("LoadTest")

    @classmethod
    def get_config(cls) -> Config:
        """Get configuration, loading it once if needed."""
        if cls._config is None:
            cls._config = get_config()
        return cls._config

    @property
    def config(self) -> Config:
        """Access configuration instance."""
        return self.get_config()

    def on_start(self) -> None:
        """Initialize user session - override in subclass."""
        self.auth_headers = self._build_auth_headers()

    def _build_auth_headers(self) -> dict[str, str]:
        """
        Build authentication headers for API requests.

        Returns:
            Dict with Content-Type, Accept, and optional Authorization headers
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        if self.config.bearer_token:
            headers["Authorization"] = f"Bearer {self.config.bearer_token}"

        return headers

    def make_payload(
        self,
        filters: Optional[dict[str, Any]] = None,
        output_fields: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Build standard API payload with project configuration.

        Args:
            filters: Optional filter parameters
            output_fields: Optional output field specifications

        Returns:
            Payload dict ready for JSON serialization
        """
        payload: dict[str, Any] = {"project": self.config.project_config}

        if filters:
            payload["filters"] = filters

        if output_fields:
            payload["outputFields"] = output_fields

        return payload

    def check_response(
        self,
        response: ResponseContextManager,
        name: str,
        success_codes: tuple[int, ...] = (200, 201),
    ) -> bool:
        """
        Validate response and mark success/failure appropriately.

        Args:
            response: Locust response context manager
            name: Request name for logging
            success_codes: HTTP status codes considered successful

        Returns:
            True if request was successful, False otherwise
        """
        if response.status_code in success_codes:
            response.success()
            return True

        # Handle specific error cases
        error_messages = {
            401: "Token expired or invalid (401 Unauthorized)",
            403: "Access forbidden (403 Forbidden)",
            404: "Resource not found (404 Not Found)",
            429: "Rate limited (429 Too Many Requests)",
            500: "Server error (500 Internal Server Error)",
            502: "Bad gateway (502)",
            503: "Service unavailable (503)",
            504: "Gateway timeout (504)",
        }

        error_msg = error_messages.get(
            response.status_code, f"HTTP {response.status_code}"
        )
        response.failure(f"{name}: {error_msg}")

        # Log auth failures at warning level
        if response.status_code in (401, 403):
            self.logger.warning(f"{name}: Authentication failed - {error_msg}")

        return False

    def think_time(self, min_seconds: float = 0.5, max_seconds: float = 2.0) -> None:
        """
        Simulate user think time with random delay.

        Args:
            min_seconds: Minimum delay in seconds
            max_seconds: Maximum delay in seconds
        """
        time.sleep(random.uniform(min_seconds, max_seconds))

    def short_pause(self) -> None:
        """Short pause between quick actions (0.5-1s)."""
        self.think_time(0.5, 1.0)

    def medium_pause(self) -> None:
        """Medium pause for typical navigation (1-2s)."""
        self.think_time(1.0, 2.0)

    def long_pause(self) -> None:
        """Long pause for complex operations (2-4s)."""
        self.think_time(2.0, 4.0)
