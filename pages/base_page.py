"""
Base page class for Playwright Page Object Model.

Provides common operations and utilities shared across all page objects.
"""

import logging
from typing import Optional

from playwright.async_api import Page, Locator

from common.config import get_config

logger = logging.getLogger(__name__)


class BasePage:
    """
    Base class for all page objects.
    
    Provides common Playwright operations with built-in timeout
    handling and error logging.
    """
    
    def __init__(self, page: Page):
        """
        Initialize the base page.
        
        Args:
            page: Playwright Page instance
        """
        self.page = page
        self.config = get_config()
    
    async def navigate(self, url: str, wait_until: str = "load") -> bool:
        """
        Navigate to a URL.
        
        Args:
            url: URL to navigate to
            wait_until: Navigation wait condition ('load', 'domcontentloaded', 'networkidle')
            
        Returns:
            True if navigation successful, False otherwise
        """
        try:
            await self.page.goto(
                url,
                wait_until=wait_until,
                timeout=self.config.page_load_timeout
            )
            logger.debug(f"Navigated to {url}")
            return True
        except Exception as e:
            logger.error(f"Navigation failed to {url}: {e}")
            return False
    
    async def click(self, selector: str, timeout: Optional[int] = None) -> bool:
        """
        Click an element.
        
        Args:
            selector: CSS or XPath selector
            timeout: Optional timeout in milliseconds
            
        Returns:
            True if click successful, False otherwise
        """
        try:
            await self.page.click(
                selector,
                timeout=timeout or self.config.element_timeout
            )
            logger.debug(f"Clicked element: {selector}")
            return True
        except Exception as e:
            logger.error(f"Click failed on {selector}: {e}")
            return False
    
    async def fill(self, selector: str, value: str, timeout: Optional[int] = None) -> bool:
        """
        Fill an input field.
        
        Args:
            selector: CSS or XPath selector
            value: Value to fill
            timeout: Optional timeout in milliseconds
            
        Returns:
            True if fill successful, False otherwise
        """
        try:
            await self.page.fill(
                selector,
                value,
                timeout=timeout or self.config.element_timeout
            )
            logger.debug(f"Filled element {selector}")
            return True
        except Exception as e:
            logger.error(f"Fill failed on {selector}: {e}")
            return False
    
    async def wait_for_selector(
        self,
        selector: str,
        state: str = "visible",
        timeout: Optional[int] = None
    ) -> Optional[Locator]:
        """
        Wait for an element to reach a certain state.
        
        Args:
            selector: CSS or XPath selector
            state: Desired state ('attached', 'detached', 'visible', 'hidden')
            timeout: Optional timeout in milliseconds
            
        Returns:
            Locator if element found, None otherwise
        """
        try:
            locator = self.page.locator(selector)
            await locator.wait_for(
                state=state,
                timeout=timeout or self.config.element_timeout
            )
            logger.debug(f"Element {selector} reached state: {state}")
            return locator
        except Exception as e:
            logger.error(f"Wait failed for {selector} ({state}): {e}")
            return None
    
    async def get_text(self, selector: str, timeout: Optional[int] = None) -> Optional[str]:
        """
        Get text content of an element.
        
        Args:
            selector: CSS or XPath selector
            timeout: Optional timeout in milliseconds
            
        Returns:
            Text content or None if element not found
        """
        try:
            locator = self.page.locator(selector)
            await locator.wait_for(timeout=timeout or self.config.element_timeout)
            return await locator.text_content()
        except Exception as e:
            logger.error(f"Get text failed for {selector}: {e}")
            return None
    
    async def is_visible(self, selector: str) -> bool:
        """
        Check if an element is visible.
        
        Args:
            selector: CSS or XPath selector
            
        Returns:
            True if element is visible, False otherwise
        """
        try:
            return await self.page.locator(selector).is_visible()
        except Exception:
            return False
    
    async def take_screenshot(self, path: str) -> bool:
        """
        Take a screenshot of the page.
        
        Args:
            path: File path to save the screenshot
            
        Returns:
            True if screenshot saved, False otherwise
        """
        try:
            await self.page.screenshot(path=path)
            logger.debug(f"Screenshot saved to {path}")
            return True
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return False
    
    @property
    def url(self) -> str:
        """Get the current page URL."""
        return self.page.url
    
    @property
    def title(self) -> str:
        """Get the current page title."""
        return self.page.title()
