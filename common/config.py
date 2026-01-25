"""
Configuration management for the load testing framework.

Provides centralized configuration via environment variables with sensible defaults.
Configured for CytoReason Platform testing.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    """
    Central configuration for load tests.
    
    All settings can be overridden via environment variables.
    Pre-configured for CytoReason Platform.
    """
    
    # CytoReason Platform URLs
    base_url: str = field(
        default_factory=lambda: os.getenv(
            "TARGET_BASE_URL",
            "https://apps.private.cytoreason.com/platform/customers/pyy"
        )
    )
    api_base_url: str = field(
        default_factory=lambda: os.getenv(
            "TARGET_API_URL",
            "https://api.platform.private.cytoreason.com/v1.0/customer/pyy/e2/platform"
        )
    )
    
    # Auth0 configuration
    auth0_domain: str = field(
        default_factory=lambda: os.getenv("AUTH0_DOMAIN", "cytoreason-pyy.eu.auth0.com")
    )
    auth0_token_url: str = field(
        default_factory=lambda: os.getenv(
            "AUTH0_TOKEN_URL",
            "https://cytoreason-pyy.eu.auth0.com/oauth/token"
        )
    )
    
    # Authentication - CytoReason credentials
    auth_token: Optional[str] = field(
        default_factory=lambda: os.getenv("AUTH_TOKEN")
    )
    default_username: str = field(
        default_factory=lambda: os.getenv("DEFAULT_USERNAME", "ui.automation@cytoreason.com")
    )
    default_password: str = field(
        default_factory=lambda: os.getenv("DEFAULT_PASSWORD", "U!a@zMatE")
    )
    
    # CytoReason specific paths
    platform_base_path: str = field(
        default_factory=lambda: os.getenv("PLATFORM_BASE_PATH", "/platform/customers/pyy")
    )
    
    # Available diseases for testing
    diseases: list = field(
        default_factory=lambda: [
            {"code": "UC", "name": "Ulcerative Colitis"},
            {"code": "CD", "name": "Crohn's Disease"},
            {"code": "CE", "name": "Celiac Disease"},
            {"code": "COPD", "name": "Chronic Obstructive Pulmonary Disease"},
            {"code": "SSC", "name": "Systemic Sclerosis"},
        ]
    )
    
    # Timeouts (milliseconds)
    page_load_timeout: int = field(
        default_factory=lambda: int(os.getenv("PAGE_LOAD_TIMEOUT_MS", "30000"))
    )
    api_timeout: int = field(
        default_factory=lambda: int(os.getenv("API_TIMEOUT_MS", "10000"))
    )
    element_timeout: int = field(
        default_factory=lambda: int(os.getenv("ELEMENT_TIMEOUT_MS", "5000"))
    )
    
    # Browser settings
    headless: bool = field(
        default_factory=lambda: os.getenv("LOCUST_PLAYWRIGHT_HEADLESS", "true").lower() == "true"
    )
    viewport_width: int = field(
        default_factory=lambda: int(os.getenv("VIEWPORT_WIDTH", "1920"))
    )
    viewport_height: int = field(
        default_factory=lambda: int(os.getenv("VIEWPORT_HEIGHT", "1080"))
    )
    
    # Load test settings
    api_user_weight: int = field(
        default_factory=lambda: int(os.getenv("API_USER_WEIGHT", "50"))
    )
    browser_user_weight: int = field(
        default_factory=lambda: int(os.getenv("BROWSER_USER_WEIGHT", "1"))
    )
    
    # Data paths
    test_data_path: str = field(
        default_factory=lambda: os.getenv("TEST_DATA_PATH", "./data")
    )
    
    @property
    def auth_headers(self) -> dict:
        """Get authentication headers for API requests."""
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers


# Singleton instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.
    
    Creates a new Config instance on first call, returns cached instance thereafter.
    """
    global _config
    if _config is None:
        _config = Config()
    return _config
