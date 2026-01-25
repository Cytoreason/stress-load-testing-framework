"""
Dashboard page object for CytoReason Platform browser automation.

Encapsulates dashboard page interactions for post-login UI testing.
"""

import logging
from typing import Optional, List

from playwright.async_api import Page

from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class DashboardPage(BasePage):
    """
    CytoReason Platform dashboard page interactions.
    
    Handles common dashboard operations for measuring client-side
    user experience under load.
    
    Dashboard Elements:
    - Statistics cards (Disease Models, Clinical Samples, Treatments, Cell Types)
    - Sidebar navigation (Disease Models, Programs, etc.)
    - CytoPedia section
    - Setup Guide section
    """
    
    # CytoReason Platform selectors
    DASHBOARD_GRAPH = "h2:has-text('See Biology Differently')"
    DASHBOARD_STATS = "[class*='stat'], p:has-text('Disease Models'), p:has-text('Clinical Samples')"
    NAVIGATION_MENU = "nav, [role='navigation']"
    USER_PROFILE = "button:has-text('U')"
    LOADING_INDICATOR = ".loading, .spinner, svg[viewBox*='0 0 300 150']"
    
    # CytoReason specific selectors
    DISEASE_MODELS_BUTTON = "button:has-text('Disease Models')"
    PROGRAMS_LINK = "a:has-text('Programs')"
    CYTOPEDIA_LINK = "a:has-text('CytoPedia')"
    HELLO_TEAM_HEADING = "h6:has-text('Hello')"
    VIEW_CYTOPEDIA_BUTTON = "button:has-text('View Cytopedia')"
    SETUP_GUIDE_LINK = "a:has-text('Open Setup Guide')"
    
    def __init__(self, page: Page):
        """
        Initialize the dashboard page.
        
        Args:
            page: Playwright Page instance
        """
        super().__init__(page)
    
    async def wait_for_dashboard_load(self, timeout: Optional[int] = None) -> bool:
        """
        Wait for the dashboard to fully load.
        
        Waits for the main dashboard graph element as specified in the plan.
        
        Args:
            timeout: Optional timeout in milliseconds
            
        Returns:
            True if dashboard loaded successfully
        """
        try:
            # Wait for loading indicator to disappear (if present)
            loading = self.page.locator(self.LOADING_INDICATOR)
            if await loading.is_visible():
                await loading.wait_for(state="hidden", timeout=timeout or self.config.page_load_timeout)
            
            # Wait for dashboard graph as per plan specification
            await self.page.wait_for_selector(
                self.DASHBOARD_GRAPH,
                timeout=timeout or self.config.page_load_timeout
            )
            logger.debug("Dashboard loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Dashboard load failed: {e}")
            return False
    
    async def get_stats_count(self) -> int:
        """
        Get the number of stats elements displayed.
        
        Useful for verifying dashboard data loaded correctly.
        
        Returns:
            Number of stats elements found
        """
        try:
            stats = self.page.locator(self.DASHBOARD_STATS)
            return await stats.count()
        except Exception:
            return 0
    
    async def navigate_to_section(self, section_name: str) -> bool:
        """
        Navigate to a dashboard section via menu.
        
        Args:
            section_name: Name or text of the section to navigate to
            
        Returns:
            True if navigation successful
        """
        try:
            # Find and click the navigation link
            nav_link = self.page.locator(f"{self.NAVIGATION_MENU} >> text={section_name}")
            await nav_link.click()
            
            # Wait for navigation to complete
            await self.page.wait_for_load_state("networkidle")
            
            logger.debug(f"Navigated to section: {section_name}")
            return True
            
        except Exception as e:
            logger.error(f"Navigation to {section_name} failed: {e}")
            return False
    
    async def refresh_data(self, refresh_selector: str = ".refresh-button, [data-refresh]") -> bool:
        """
        Trigger a data refresh on the dashboard.
        
        Args:
            refresh_selector: Selector for the refresh button
            
        Returns:
            True if refresh triggered successfully
        """
        try:
            await self.click(refresh_selector)
            await self.page.wait_for_load_state("networkidle")
            logger.debug("Dashboard data refreshed")
            return True
        except Exception as e:
            logger.error(f"Dashboard refresh failed: {e}")
            return False
    
    async def is_user_logged_in(self) -> bool:
        """
        Check if user profile element is visible (indicates logged in).
        
        Returns:
            True if user appears to be logged in
        """
        return await self.is_visible(self.USER_PROFILE)
    
    async def get_visible_sections(self) -> List[str]:
        """
        Get list of visible dashboard sections.
        
        Returns:
            List of section names/identifiers
        """
        sections = []
        try:
            nav_items = self.page.locator(f"{self.NAVIGATION_MENU} a, {self.NAVIGATION_MENU} button")
            count = await nav_items.count()
            for i in range(count):
                text = await nav_items.nth(i).text_content()
                if text:
                    sections.append(text.strip())
        except Exception as e:
            logger.error(f"Failed to get sections: {e}")
        return sections
    
    async def wait_for_element(self, selector: str, timeout: Optional[int] = None) -> bool:
        """
        Wait for a specific dashboard element.
        
        Args:
            selector: CSS or XPath selector
            timeout: Optional timeout in milliseconds
            
        Returns:
            True if element appeared, False otherwise
        """
        element = await self.wait_for_selector(selector, timeout=timeout)
        return element is not None
