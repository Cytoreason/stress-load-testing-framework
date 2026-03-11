"""
Base page helpers shared by all page objects.

Provides resilient navigation with automatic re-authentication on Auth0
redirect, configurable retries, and consistent wait strategies.
"""
from __future__ import annotations

from playwright.async_api import Locator, Page, TimeoutError as PlaywrightTimeoutError

from src.config import settings
from src.ui.selectors import login_sel


class BasePage:
    """Shared navigation and interaction utilities for all page objects."""

    def __init__(self, page: Page) -> None:
        self.page = page

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    async def goto_url(
        self,
        url: str,
        ready_locator: Locator,
        *,
        retries: int = 2,
    ) -> None:
        """
        Navigate to *url* and wait for *ready_locator* to become visible.

        If Auth0 redirects us away, re-authenticate transparently and retry.
        Raises ``PlaywrightTimeoutError`` only after all retries are exhausted.
        """
        timeout_ms = max(settings.navigation_timeout_ms, 60_000)
        path = url.replace(settings.base_url, "")
        url_pattern = f"**{path}**" if path else f"**{settings.base_url}**"

        for attempt in range(retries + 1):
            await self.page.goto(url, wait_until="domcontentloaded")
            await self._recover_auth_if_needed()

            try:
                await self.page.wait_for_url(
                    url_pattern,
                    wait_until="domcontentloaded",
                    timeout=timeout_ms,
                )
                await ready_locator.wait_for(state="visible", timeout=timeout_ms)
                return
            except PlaywrightTimeoutError:
                if attempt < retries:
                    await self.page.reload(wait_until="domcontentloaded")
                    await self._recover_auth_if_needed()
                else:
                    raise

    async def _recover_auth_if_needed(self) -> None:
        """Re-enter credentials when the page unexpectedly lands on Auth0."""
        if "auth0.com" not in self.page.url:
            return
        # Lazy import to avoid circular dependency
        from src.ui.pages.login_page import LoginPage  # noqa: PLC0415

        await LoginPage(self.page).login()

    # ------------------------------------------------------------------
    # Interaction helpers
    # ------------------------------------------------------------------

    async def click_and_wait_domcontentloaded(self, locator: Locator) -> None:
        """Click a locator and wait for the DOM to settle."""
        async with self.page.expect_navigation(
            wait_until="domcontentloaded",
            timeout=settings.navigation_timeout_ms,
        ):
            await locator.click()

    async def safe_click(self, locator: Locator, *, timeout_ms: int | None = None) -> None:
        """Click after ensuring the element is visible."""
        await locator.wait_for(
            state="visible", timeout=timeout_ms or settings.default_timeout_ms
        )
        await locator.click()

    async def fill_and_wait(
        self,
        locator: Locator,
        text: str,
        *,
        debounce_ms: int = 300,
    ) -> None:
        """Fill a text field and wait for any search debounce to settle."""
        await locator.wait_for(state="visible", timeout=settings.default_timeout_ms)
        await locator.fill(text)
        if debounce_ms:
            await self.page.wait_for_timeout(debounce_ms)
