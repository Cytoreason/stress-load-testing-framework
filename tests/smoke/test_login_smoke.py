"""
Smoke test: Auth0 login flow.

Validates that:
1. Navigating to the base URL eventually lands on Auth0 (or the app if
   session cookies are present).
2. Submitting valid credentials redirects back to the platform.
3. The post-login landing page contains the expected navigation element.

Run before any load/stress test to confirm the auth path is healthy.
"""
from __future__ import annotations

import pytest
from playwright.async_api import Page, expect

from src.config import settings
from src.ui.pages.login_page import LoginPage
from src.ui.selectors import ready_sel


@pytest.mark.smoke
@pytest.mark.ui
async def test_auth0_login_redirects_to_app(page: Page) -> None:
    """
    Navigate to the platform.  If Auth0 intercepts, log in and confirm
    we land back on the platform URL.
    """
    lp = LoginPage(page)
    await lp.goto()

    if "auth0.com" in page.url:
        await lp.login()

    # Must end up on the platform, not stuck on Auth0
    await page.wait_for_url(
        f"**{settings.base_url}/**",
        wait_until="domcontentloaded",
        timeout=settings.navigation_timeout_ms,
    )
    assert "auth0.com" not in page.url, (
        f"Post-login URL still contains auth0.com: {page.url}"
    )


@pytest.mark.smoke
@pytest.mark.ui
async def test_post_login_landing_element_visible(page: Page) -> None:
    """
    After login the authenticated landing element (Programs nav link) must
    be visible – confirms the app loaded, not just a blank redirect.
    """
    # Navigate; session cookie from authenticated_context means no re-login
    await page.goto(settings.base_url, wait_until="domcontentloaded")

    landing = page.get_by_role(
        ready_sel.landing_unique_role,
        name=ready_sel.landing_unique_name,
    )
    await expect(landing).to_be_visible(timeout=10_000)
