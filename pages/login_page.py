"""
Login page object for Playwright browser automation.

Encapsulates login page interactions for CytoReason Platform.
CytoReason uses Auth0 for authentication.
"""

import logging
from typing import Optional

from playwright.async_api import Page

from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class LoginPage(BasePage):
    """
    Login page interactions for CytoReason Platform.
    
    CytoReason uses Auth0 authentication which redirects to:
    cytoreason-pyy.eu.auth0.com
    
    Handles user authentication via browser forms with Playwright's
    auto-wait feature for stability under load.
    """
    
    # Auth0 Login Selectors
    USERNAME_INPUT = "input[name='username'], input[name='email'], input#username"
    PASSWORD_INPUT = "input[name='password'], input#password"
    SUBMIT_BUTTON = "button[type='submit'], button[name='action'], button:has-text('Continue'), button:has-text('Log In')"
    ERROR_MESSAGE = ".error-message, .alert-danger, [role='alert'], .ulp-input-error-message"
    
    # CytoReason specific
    LOADING_SPINNER = ".loading, .spinner, svg[viewBox]"
    AUTH0_FORM = "form[data-provider='auth0'], .auth0-lock-form"
    
    def __init__(self, page: Page):
        """
        Initialize the login page.
        
        Args:
            page: Playwright Page instance
        """
        super().__init__(page)
    
    async def navigate(self, url: str) -> bool:
        """
        Navigate to the login page.
        
        Args:
            url: Base URL or full login URL
            
        Returns:
            True if navigation successful
        """
        # Handle both base URL and full login URL
        login_url = url if "/login" in url else f"{url.rstrip('/')}/login"
        return await super().navigate(login_url)
    
    async def login(self, username: str, password: str) -> bool:
        """
        Perform login operation.
        
        Uses Playwright's auto-wait feature for stability under load.
        Click and wait for navigation in one go as per plan specification.
        
        Args:
            username: Login username
            password: Login password
            
        Returns:
            True if login appears successful, False otherwise
        """
        try:
            # Fill username
            await self.page.fill(self.USERNAME_INPUT, username)
            
            # Fill password
            await self.page.fill(self.PASSWORD_INPUT, password)
            
            # Click and wait for navigation in one go
            async with self.page.expect_navigation():
                await self.page.click(self.SUBMIT_BUTTON)
            
            logger.info(f"Login submitted for user: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Login failed for {username}: {e}")
            return False
    
    async def login_and_verify(self, username: str, password: str, success_selector: str) -> bool:
        """
        Perform login and verify success.
        
        Args:
            username: Login username
            password: Login password
            success_selector: Selector that indicates successful login
            
        Returns:
            True if login successful and verified, False otherwise
        """
        if not await self.login(username, password):
            return False
        
        # Verify login success by checking for expected element
        element = await self.wait_for_selector(success_selector)
        if element:
            logger.info(f"Login verified for user: {username}")
            return True
        
        logger.warning(f"Login verification failed for user: {username}")
        return False
    
    async def get_error_message(self) -> Optional[str]:
        """
        Get any displayed error message.
        
        Returns:
            Error message text or None if no error displayed
        """
        if await self.is_visible(self.ERROR_MESSAGE):
            return await self.get_text(self.ERROR_MESSAGE)
        return None
    
    async def is_login_page(self) -> bool:
        """
        Check if currently on the login page.
        
        Returns:
            True if login form elements are visible
        """
        return (
            await self.is_visible(self.USERNAME_INPUT) and
            await self.is_visible(self.PASSWORD_INPUT)
        )
