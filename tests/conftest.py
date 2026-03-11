"""
Pytest conftest – fixtures and shared configuration for all test suites.

Provides:
  - ``browser_context`` fixture: one Auth0-authenticated browser context per
    test module (session-scoped to avoid repeated logins in smoke runs).
  - ``page`` fixture: a fresh page per test, sharing the authenticated context.
  - Marker definitions (smoke, ui, load, stress, selector).
  - ``base_url`` CLI option propagation for pytest-playwright compatibility.

Authentication strategy in tests:
  Tests re-use a single browser context per pytest session.  Auth0 login
  is performed once in ``authenticated_context`` and shared via the context
  fixture.  This matches how a real user would behave and avoids hammering
  Auth0 repeatedly during smoke validation.
"""
from __future__ import annotations

import pytest
from playwright.async_api import BrowserContext, Page, async_playwright

from src.config import settings
from src.ui.pages.login_page import LoginPage
from src.ui.selectors import login_sel, ready_sel


# ---------------------------------------------------------------------------
# pytest-playwright base_url hook
# ---------------------------------------------------------------------------

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "smoke: fast pre-flight check; must pass before any load run",
    )
    config.addinivalue_line(
        "markers",
        "ui: full browser-driven UI interaction test",
    )
    config.addinivalue_line(
        "markers",
        "load: drives a Locust load test profile",
    )
    config.addinivalue_line(
        "markers",
        "stress: drives a Locust stress/ramp-to-break profile",
    )
    config.addinivalue_line(
        "markers",
        "selector: validates that a DOM selector is still present on the live page",
    )


# ---------------------------------------------------------------------------
# Base URL hook (integrates with --base-url pytest-playwright CLI option)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def base_url() -> str:
    return settings.base_url


# ---------------------------------------------------------------------------
# Authenticated browser context (session-scoped – one login for all tests)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
async def authenticated_context(base_url: str):
    """
    Launch a real Chromium browser, perform Auth0 login once, and yield the
    authenticated BrowserContext.  Teardown closes the browser cleanly.
    """
    async with async_playwright() as playwright:
        browser = await getattr(playwright, settings.browser).launch(
            headless=settings.headless,
        )
        ctx: BrowserContext = await browser.new_context(
            base_url=base_url,
            viewport=settings.viewport,
            ignore_https_errors=True,
        )

        # Block media/fonts for speed
        async def route_handler(route, request):
            if request.resource_type in ("image", "media", "font"):
                await route.abort()
            else:
                await route.continue_()

        await ctx.route("**/*", route_handler)

        login_page_obj = await ctx.new_page()
        login_page_obj.set_default_timeout(settings.default_timeout_ms)
        login_page_obj.set_default_navigation_timeout(settings.navigation_timeout_ms)

        lp = LoginPage(login_page_obj)
        await lp.goto()

        if "auth0.com" in login_page_obj.url:
            await lp.login()
        else:
            try:
                await login_page_obj.get_by_label(
                    login_sel.username_input_label
                ).wait_for(state="visible", timeout=5_000)
                await lp.login()
            except Exception:
                pass  # Already authenticated

        # Verify authentication succeeded
        await login_page_obj.wait_for_url(
            f"**{base_url}/**",
            wait_until="domcontentloaded",
            timeout=settings.navigation_timeout_ms,
        )
        await login_page_obj.get_by_role(
            ready_sel.landing_unique_role,
            name=ready_sel.landing_unique_name,
        ).wait_for(state="visible", timeout=10_000)
        await login_page_obj.close()

        yield ctx

        await browser.close()


# ---------------------------------------------------------------------------
# Per-test page (reuses the authenticated context)
# ---------------------------------------------------------------------------

@pytest.fixture
async def page(authenticated_context: BrowserContext) -> Page:
    """
    Open a fresh page within the authenticated context.

    Using the shared context means the Auth0 session cookies are already
    present – no re-login needed per test.
    """
    p = await authenticated_context.new_page()
    p.set_default_timeout(settings.default_timeout_ms)
    p.set_default_navigation_timeout(settings.navigation_timeout_ms)
    yield p
    await p.close()
