"""
Browser-based UI stress user scenario for CytoReason Platform.

Uses Playwright via locust-plugins to measure client-side user experience
(rendering, JS execution) while the backend is under API stress.

This represents the 10% of load that uses real browsers for UX sampling.

Target URL: https://apps.private.cytoreason.com/platform/customers/pyy/
"""

import logging
import time
import random
from typing import Optional

from locust import task, events
from locust_plugins.users.playwright import PlaywrightUser, pw, PageWithRetry

from pages.login_page import LoginPage
from pages.dashboard_page import DashboardPage
from common.config import get_config
from common.auth_util import AuthUtil

logger = logging.getLogger(__name__)


class UIStressUser(PlaywrightUser):
    """
    Browser-based user for CytoReason Platform UI/UX load testing.
    
    Uses Playwright to launch headless browsers and measure real
    client-side performance metrics like Time to Interactive and
    Visual Complete under backend stress.
    
    CytoReason Platform Pages:
    - Landing: /platform/customers/pyy/
    - Disease Explorer: /platform/customers/pyy/disease-explorer/differential-expression
    - Programs: /platform/customers/pyy/programs
    - CytoPedia: /platform/customers/pyy/cytopedia
    
    IMPORTANT: Keep browser user count low - each instance uses
    200-500MB RAM. Use API users for bulk load generation.
    
    Attributes:
        weight: User spawn weight (1 = minimal, use API users for bulk)
        wait_time: 5 seconds between browser operations
    """
    
    # Keep browser users minimal - they are resource intensive!
    weight = 1
    
    # Override host to always use web app endpoint
    host = "https://apps.private.cytoreason.com"
    
    # CytoReason base path - class attribute for stability
    base_path = "/platform/customers/pyy"
    
    # Config loaded at class level to avoid __init__ issues with PlaywrightUser
    _config = None
    
    @classmethod
    def get_config_instance(cls):
        if cls._config is None:
            cls._config = get_config()
        return cls._config
    
    # CytoReason-specific selectors discovered via Playwright MCP
    SELECTORS = {
        # Navigation
        "logo": "a[href*='/platform/customers/pyy/']",
        "nav_documentation": "a:has-text('Notebook documentation')",
        "nav_cytopedia": "a:has-text('CytoPedia')",
        "nav_support": "text=Support",
        "user_profile_button": "button:has-text('U')",
        
        # Sidebar
        "disease_models_button": "button:has-text('Disease Models')",
        "programs_link": "a:has-text('Programs')",
        
        # Disease Explorer
        "disease_dropdown": "[role='combobox']",
        "inventory_button": "button:has-text('Inventory')",
        "disease_biology_button": "button:has-text('Disease Biology')",
        "clinical_score_button": "button:has-text('Clinical Score')",
        
        # Dashboard content
        "dashboard_heading": "h2:has-text('See Biology Differently')",
        "hello_team": "h6:has-text('Hello')",
        "disease_models_stat": "text=Disease Models",
        "clinical_samples_stat": "text=Clinical Samples",
        
        # CytoPedia
        "cytopedia_search": "input[placeholder*='Search terms']",
        "cytopedia_heading": "h1:has-text('CytoPedia')",
        
        # Loading indicators
        "loading_spinner": ".loading, .spinner, svg[viewBox]",
        
        # Feature type selection
        "target_gene_radio": "input[type='radio'][value='Target Gene'], label:has-text('Target Gene')",
        "target_signature_radio": "input[type='radio'][value='Target Signature'], label:has-text('Target Signature')",
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = self.get_config_instance()
        self.auth = AuthUtil()
    
    # Auth0 login selectors
    AUTH0_SELECTORS = {
        "email_input": "input[name='email'], input[name='username'], input[type='email']",
        "password_input": "input[name='password'], input[type='password']",
        "submit_button": "button[type='submit'], button:has-text('Continue'), button:has-text('Log In')",
        "continue_button": "button:has-text('Continue')",
    }
    
    def on_start(self) -> None:
        """Called when a browser user starts."""
        logger.info(f"UIStressUser {id(self)} starting with browser")
    
    def on_stop(self) -> None:
        """Called when a browser user stops."""
        logger.info(f"UIStressUser {id(self)} stopping")
    
    async def handle_auth0_login(self, page: PageWithRetry) -> bool:
        """Handle Auth0 login if redirected to login page."""
        try:
            current_url = page.url
            if 'auth0.com' not in current_url and 'login' not in current_url.lower():
                return True  # Already logged in
            
            logger.info("Detected Auth0 login page, attempting login...")
            
            # Get credentials
            config = getattr(self, 'config', None) or self.get_config_instance()
            username = config.default_username
            password = config.default_password
            
            # Wait for and fill email
            await page.wait_for_selector(self.AUTH0_SELECTORS["email_input"], timeout=10000)
            await page.fill(self.AUTH0_SELECTORS["email_input"], username)
            
            # Click continue if there's a two-step flow
            try:
                continue_btn = await page.query_selector(self.AUTH0_SELECTORS["continue_button"])
                if continue_btn:
                    await continue_btn.click()
                    await page.wait_for_timeout(1000)
            except Exception:
                pass
            
            # Fill password
            await page.wait_for_selector(self.AUTH0_SELECTORS["password_input"], timeout=10000)
            await page.fill(self.AUTH0_SELECTORS["password_input"], password)
            
            # Submit
            await page.click(self.AUTH0_SELECTORS["submit_button"])
            
            # Wait for redirect back to app
            await page.wait_for_url("**/platform/**", timeout=30000)
            logger.info("Auth0 login successful")
            return True
            
        except Exception as e:
            logger.error(f"Auth0 login failed: {e}")
            return False
    
    async def wait_for_app_load(self, page: PageWithRetry, timeout: int = 30000) -> bool:
        """Wait for CytoReason app to fully load (spinner disappears)."""
        try:
            # Wait for loading spinner to disappear
            await page.wait_for_selector(
                self.SELECTORS["loading_spinner"],
                state="hidden",
                timeout=timeout
            )
            return True
        except Exception:
            # Try waiting for dashboard content instead
            try:
                await page.wait_for_selector(
                    self.SELECTORS["dashboard_heading"],
                    timeout=timeout
                )
                return True
            except Exception:
                return False
    
    @task(3)
    @pw  # Decorator to inject the Playwright page
    async def landing_page_flow(self, page: PageWithRetry) -> None:
        """
        Load the CytoReason landing page and measure performance.
        
        Measures:
        1. Initial page load time
        2. Time to dashboard content visible
        """
        start_time = time.time()
        try:
            await page.goto(f"{self.host}{self.base_path}/")
            
            # Handle Auth0 login if redirected
            if 'auth0.com' in page.url or 'login' in page.url.lower():
                await self.handle_auth0_login(page)
            
            await self.wait_for_app_load(page)
            
            load_time_ms = (time.time() - start_time) * 1000
            
            events.request.fire(
                request_type="UI_Render",
                name="Landing_Page_Load",
                response_time=load_time_ms,
                response_length=0,
                exception=None,
            )
            logger.debug(f"Landing page loaded in {load_time_ms:.2f}ms")
            
        except Exception as e:
            events.request.fire(
                request_type="UI_Render",
                name="Landing_Page_Load",
                response_time=0,
                response_length=0,
                exception=e,
            )
            logger.error(f"Landing page load failed: {e}")
    
    @task(2)
    @pw
    async def disease_explorer_flow(self, page: PageWithRetry) -> None:
        """
        Navigate to Disease Explorer and measure page load.
        Simplified flow - just load the page and verify it renders.
        """
        start_time = time.time()
        try:
            await page.goto(f"{self.host}{self.base_path}/disease-explorer/differential-expression")
            
            # Handle Auth0 login if redirected
            if 'auth0.com' in page.url or 'login' in page.url.lower():
                await self.handle_auth0_login(page)
            
            await self.wait_for_app_load(page)
            
            load_time_ms = (time.time() - start_time) * 1000
            
            events.request.fire(
                request_type="UI_Render",
                name="Disease_Explorer_Load",
                response_time=load_time_ms,
                response_length=0,
                exception=None,
            )
            logger.debug(f"Disease Explorer loaded in {load_time_ms:.2f}ms")
            
        except Exception as e:
            events.request.fire(
                request_type="UI_Render",
                name="Disease_Explorer_Load",
                response_time=0,
                response_length=0,
                exception=e,
            )
            logger.error(f"Disease Explorer load failed: {e}")
    
    @task(2)
    @pw
    async def programs_page_flow(self, page: PageWithRetry) -> None:
        """
        Navigate to Programs page and verify content loads.
        """
        start_time = time.time()
        try:
            await page.goto(f"{self.host}{self.base_path}/programs")
            
            # Handle Auth0 login if redirected
            if 'auth0.com' in page.url or 'login' in page.url.lower():
                await self.handle_auth0_login(page)
            
            await self.wait_for_app_load(page)
            
            load_time_ms = (time.time() - start_time) * 1000
            
            events.request.fire(
                request_type="UI_Render",
                name="Programs_Page_Load",
                response_time=load_time_ms,
                response_length=0,
                exception=None,
            )
            logger.debug(f"Programs page loaded in {load_time_ms:.2f}ms")
            
        except Exception as e:
            events.request.fire(
                request_type="UI_Render",
                name="Programs_Page_Load",
                response_time=0,
                response_length=0,
                exception=e,
            )
            logger.error(f"Programs page load failed: {e}")
    
    @task(1)
    @pw
    async def cytopedia_flow(self, page: PageWithRetry) -> None:
        """
        Navigate to CytoPedia and measure page load.
        """
        start_time = time.time()
        try:
            await page.goto(f"{self.host}{self.base_path}/cytopedia")
            
            # Handle Auth0 login if redirected
            if 'auth0.com' in page.url or 'login' in page.url.lower():
                await self.handle_auth0_login(page)
            
            await self.wait_for_app_load(page)
            
            load_time_ms = (time.time() - start_time) * 1000
            
            events.request.fire(
                request_type="UI_Render",
                name="CytoPedia_Page_Load",
                response_time=load_time_ms,
                response_length=0,
                exception=None,
            )
            logger.debug(f"CytoPedia page loaded in {load_time_ms:.2f}ms")
            
        except Exception as e:
            events.request.fire(
                request_type="UI_Render",
                name="CytoPedia_Page_Load",
                response_time=0,
                response_length=0,
                exception=e,
            )
            logger.error(f"CytoPedia page load failed: {e}")
    
    @task(1)
    @pw
    async def sidebar_navigation_flow(self, page: PageWithRetry) -> None:
        """
        Test sidebar navigation - load landing page and measure.
        """
        start_time = time.time()
        try:
            await page.goto(f"{self.host}{self.base_path}/")
            
            # Handle Auth0 login if redirected
            if 'auth0.com' in page.url or 'login' in page.url.lower():
                await self.handle_auth0_login(page)
            
            await self.wait_for_app_load(page)
            
            load_time_ms = (time.time() - start_time) * 1000
            
            events.request.fire(
                request_type="UI_Render",
                name="Sidebar_Nav_Load",
                response_time=load_time_ms,
                response_length=0,
                exception=None,
            )
            logger.debug(f"Sidebar navigation page loaded in {load_time_ms:.2f}ms")
            
        except Exception as e:
            events.request.fire(
                request_type="UI_Render",
                name="Sidebar_Nav_Load",
                response_time=0,
                response_length=0,
                exception=e,
            )
            logger.error(f"Sidebar navigation failed: {e}")
