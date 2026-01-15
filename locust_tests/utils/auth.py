"""
Authentication utilities for load testing
"""
from typing import Dict, Optional


class AuthHandler:
    """Handle various authentication methods"""

    @staticmethod
    def get_bearer_token_headers(token: str) -> Dict[str, str]:
        """
        Get headers for Bearer token authentication

        Args:
            token: Authentication token

        Returns:
            Dictionary with Authorization header
        """
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    def get_basic_auth_headers(username: str, password: str) -> Dict[str, str]:
        """
        Get headers for Basic authentication

        Args:
            username: Username
            password: Password

        Returns:
            Dictionary with Authorization header
        """
        import base64
        credentials = f"{username}:{password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return {"Authorization": f"Basic {encoded}"}

    @staticmethod
    def get_api_key_headers(api_key: str, header_name: str = "X-API-Key") -> Dict[str, str]:
        """
        Get headers for API key authentication

        Args:
            api_key: API key
            header_name: Header name for the API key

        Returns:
            Dictionary with API key header
        """
        return {header_name: api_key}

    @staticmethod
    def get_custom_headers(headers: Dict[str, str]) -> Dict[str, str]:
        """
        Get custom headers

        Args:
            headers: Custom headers dictionary

        Returns:
            Headers dictionary
        """
        return headers


def get_auth_headers(
    auth_type: str = "token",
    token: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    api_key: Optional[str] = None,
    custom_headers: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """
    Get authentication headers based on auth type

    Args:
        auth_type: Type of authentication (token, basic, api_key, custom, none)
        token: Bearer token
        username: Username for basic auth
        password: Password for basic auth
        api_key: API key
        custom_headers: Custom headers dictionary

    Returns:
        Authentication headers dictionary
    """
    auth_handler = AuthHandler()

    if auth_type == "token" and token:
        return auth_handler.get_bearer_token_headers(token)
    elif auth_type == "basic" and username and password:
        return auth_handler.get_basic_auth_headers(username, password)
    elif auth_type == "api_key" and api_key:
        return auth_handler.get_api_key_headers(api_key)
    elif auth_type == "custom" and custom_headers:
        return auth_handler.get_custom_headers(custom_headers)
    else:
        return {}
