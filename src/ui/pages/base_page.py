"""
Base page helpers shared by all page objects.

Provides resilient navigation with automatic re-authentication on Auth0
redirect, configurable retries, and consistent wait strategies.
"""
from __future__ import annotations

from playwright.async_api import Error as PlaywrightError
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
        ready_locator: Locator | None = None,
        *,
        retries: int = 2,
        ready_timeout_ms: int | None = None,
    ) -> None:
        """
        Navigate to *url* and wait for *ready_locator* to become visible.

        Parameters
        ----------
        retries:
            Number of retry attempts after the first failure (default 2).
        ready_timeout_ms:
            Timeout for the ready-locator wait specifically.  Defaults to
            ``navigation_timeout_ms`` floored at 60 s.  Pass a higher value
            for pages whose API-driven content takes longer to appear
            (e.g. the DX page model picker needs up to 90 s under load).

        Navigation (goto + wait_for_url) always uses a 60 s floor.
        Transient network errors and timeouts are both retried.
        """
        nav_timeout_ms = max(settings.navigation_timeout_ms, 60_000)
        _ready_timeout_ms = ready_timeout_ms or nav_timeout_ms
        path = url.replace(settings.base_url, "")
        url_pattern = f"**{path}**" if path else f"**{settings.base_url}**"

        last_err: Exception | None = None
        for attempt in range(retries + 1):
            try:
                await self.page.goto(url, wait_until="domcontentloaded", timeout=nav_timeout_ms)
                await self._recover_auth_if_needed()
                await self.page.wait_for_url(
                    url_pattern,
                    wait_until="domcontentloaded",
                    timeout=nav_timeout_ms,
                )
                if ready_locator is not None:
                    await ready_locator.wait_for(state="visible", timeout=_ready_timeout_ms)
                return
            except (PlaywrightTimeoutError, PlaywrightError) as exc:
                last_err = exc
                if attempt < retries:
                    await self.page.wait_for_timeout(1_000)

        raise last_err  # type: ignore[misc]

    async def _recover_auth_if_needed(self) -> None:
        """Re-enter credentials when the page unexpectedly lands on Auth0.

        Also handles the OAuth callback URL (``/signed-in?code=``) that appears
        after a silent Auth0 token refresh — the SPA redirects to Auth0 and back
        without user interaction; we wait for the app to complete that redirect,
        falling back to navigating home if it stalls.
        """
        url = self.page.url
        if "auth0.com" in url:
            from src.ui.pages.login_page import LoginPage  # noqa: PLC0415
            await LoginPage(self.page).login()
        elif "/signed-in" in url:
            # Silent token refresh completed — wait for SPA to redirect back
            try:
                await self.page.wait_for_url(
                    f"**{settings.base_url}**",
                    wait_until="domcontentloaded",
                    timeout=20_000,
                )
            except (PlaywrightTimeoutError, PlaywrightError):
                await self.page.goto(
                    settings.base_url, wait_until="domcontentloaded", timeout=30_000
                )

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
