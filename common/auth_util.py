"""
Shared authentication utilities for load testing.

Provides common login logic and token management used by both
API and browser-based test scenarios.
"""

import logging
from typing import Optional, Tuple
from collections import deque

from common.config import get_config

logger = logging.getLogger(__name__)


class AuthUtil:
    """
    Authentication utility class.
    
    Handles login operations, token management, and credential rotation
    for load testing scenarios.
    """
    
    def __init__(self):
        self.config = get_config()
        self._credentials_queue: deque = deque()
        self._current_token: Optional[str] = None
    
    def load_credentials(self, credentials: list[Tuple[str, str]]) -> None:
        """
        Load a list of credentials for rotation.
        
        Uses a deque to ensure unique credentials per worker,
        preventing conflicts when multiple users edit the same record.
        
        Args:
            credentials: List of (username, password) tuples
        """
        self._credentials_queue = deque(credentials)
        logger.info(f"Loaded {len(credentials)} credential sets")
    
    def get_next_credentials(self) -> Tuple[str, str]:
        """
        Get the next available credentials from the queue.
        
        Uses round-robin rotation to distribute credentials across workers.
        Falls back to default credentials if queue is empty.
        
        Returns:
            Tuple of (username, password)
        """
        if self._credentials_queue:
            creds = self._credentials_queue.popleft()
            self._credentials_queue.append(creds)  # Re-add for rotation
            return creds
        return (self.config.default_username, self.config.default_password)
    
    def get_auth_headers(self, token: Optional[str] = None) -> dict:
        """
        Get authentication headers for API requests.
        
        Args:
            token: Optional bearer token. Uses config token if not provided.
            
        Returns:
            Dict with Authorization and Content-Type headers
        """
        headers = {"Content-Type": "application/json"}
        auth_token = token or self._current_token or self.config.auth_token
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        return headers
    
    def set_token(self, token: str) -> None:
        """
        Set the current authentication token.
        
        Args:
            token: The bearer token to use for subsequent requests
        """
        self._current_token = token
        logger.debug("Authentication token updated")
    
    def clear_token(self) -> None:
        """Clear the current authentication token."""
        self._current_token = None
        logger.debug("Authentication token cleared")
    
    async def login_api(self, client, username: str, password: str) -> Optional[str]:
        """
        Perform API-based login and extract token.
        
        Args:
            client: HTTP client (Locust or requests-like)
            username: Login username
            password: Login password
            
        Returns:
            Authentication token if successful, None otherwise
        """
        try:
            response = client.post(
                "/api/v1/auth/login",
                json={"username": username, "password": password},
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                data = response.json()
                token = data.get("token") or data.get("access_token")
                if token:
                    self.set_token(token)
                    logger.info(f"API login successful for {username}")
                    return token
            logger.warning(f"API login failed for {username}: {response.status_code}")
        except Exception as e:
            logger.error(f"API login error for {username}: {e}")
        return None
    
    async def login_browser(self, page, username: str, password: str) -> bool:
        """
        Perform browser-based login via Playwright.
        
        Args:
            page: Playwright page instance
            username: Login username  
            password: Login password
            
        Returns:
            True if login successful, False otherwise
        """
        try:
            await page.fill("input[name='username']", username)
            await page.fill("input[name='password']", password)
            
            async with page.expect_navigation():
                await page.click("button[type='submit']")
            
            logger.info(f"Browser login successful for {username}")
            return True
        except Exception as e:
            logger.error(f"Browser login error for {username}: {e}")
            return False
