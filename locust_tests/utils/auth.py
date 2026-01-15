"""
Authentication utilities for load testing
"""
from typing import Dict, Optional
import requests
import time
from datetime import datetime, timedelta


class Auth0TokenManager:
    """Manage Auth0 OAuth2 tokens with automatic refresh"""

    def __init__(
        self,
        domain: str,
        client_id: str,
        client_secret: str,
        audience: Optional[str] = None
    ):
        """
        Initialize Auth0 token manager

        Args:
            domain: Auth0 domain (e.g., cytoreason-pxx.us.auth0.com)
            client_id: Auth0 client ID
            client_secret: Auth0 client secret
            audience: API audience/identifier
        """
        self.domain = domain
        self.client_id = client_id
        self.client_secret = client_secret
        self.audience = audience
        self.token_url = f"https://{domain}/oauth/token"

        self._access_token = None
        self._token_expires_at = None

    def get_token(self, force_refresh: bool = False) -> str:
        """
        Get access token, refreshing if necessary

        Args:
            force_refresh: Force token refresh even if not expired

        Returns:
            Access token string
        """
        if force_refresh or self._is_token_expired():
            self._refresh_token()

        return self._access_token

    def _is_token_expired(self) -> bool:
        """Check if current token is expired or will expire soon"""
        if not self._access_token or not self._token_expires_at:
            return True

        # Refresh if token expires in less than 5 minutes
        return datetime.now() >= self._token_expires_at - timedelta(minutes=5)

    def _refresh_token(self):
        """Request new access token from Auth0"""
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        }

        if self.audience:
            payload["audience"] = self.audience

        try:
            response = requests.post(
                self.token_url,
                json=payload,
                headers={"content-type": "application/json"},
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            self._access_token = data["access_token"]

            # Calculate token expiration time
            expires_in = data.get("expires_in", 86400)  # Default 24 hours
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)

        except requests.RequestException as e:
            raise Exception(f"Failed to get Auth0 token: {e}")

    def get_headers(self) -> Dict[str, str]:
        """Get authorization headers with current token"""
        token = self.get_token()
        return {"Authorization": f"Bearer {token}"}


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
    custom_headers: Optional[Dict[str, str]] = None,
    auth0_domain: Optional[str] = None,
    auth0_client_id: Optional[str] = None,
    auth0_client_secret: Optional[str] = None,
    auth0_audience: Optional[str] = None
) -> Dict[str, str]:
    """
    Get authentication headers based on auth type

    Args:
        auth_type: Type of authentication (token, basic, api_key, auth0, custom, none)
        token: Bearer token
        username: Username for basic auth
        password: Password for basic auth
        api_key: API key
        custom_headers: Custom headers dictionary
        auth0_domain: Auth0 domain for OAuth2
        auth0_client_id: Auth0 client ID
        auth0_client_secret: Auth0 client secret
        auth0_audience: Auth0 API audience

    Returns:
        Authentication headers dictionary
    """
    auth_handler = AuthHandler()

    if auth_type == "auth0" and auth0_domain and auth0_client_id and auth0_client_secret:
        # Create Auth0 token manager and get headers
        token_manager = Auth0TokenManager(
            domain=auth0_domain,
            client_id=auth0_client_id,
            client_secret=auth0_client_secret,
            audience=auth0_audience
        )
        return token_manager.get_headers()
    elif auth_type == "token" and token:
        return auth_handler.get_bearer_token_headers(token)
    elif auth_type == "basic" and username and password:
        return auth_handler.get_basic_auth_headers(username, password)
    elif auth_type == "api_key" and api_key:
        return auth_handler.get_api_key_headers(api_key)
    elif auth_type == "custom" and custom_headers:
        return auth_handler.get_custom_headers(custom_headers)
    else:
        return {}


def create_auth0_token_manager_from_env() -> Optional[Auth0TokenManager]:
    """
    Create Auth0TokenManager from environment variables

    Returns:
        Auth0TokenManager instance or None if credentials not found
    """
    import os

    domain = os.getenv("AUTH0_PXX_DOMAIN") or os.getenv("AUTH0_PYY_DOMAIN")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    audience = os.getenv("AUTH0_AUDIENCE", "https://apps.private.cytoreason.com/")

    if domain and client_id and client_secret:
        return Auth0TokenManager(
            domain=domain,
            client_id=client_id,
            client_secret=client_secret,
            audience=audience
        )

    return None
