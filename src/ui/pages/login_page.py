"""
Auth0 Login page object.

LIVE VALIDATED (2026-03-11):
- Auth0 tenant: cytoreason-pyy.eu.auth0.com
- Email field: input[name="username"] type=text  → get_by_label("Email address *") ✓
- Password field: input[name="password"] type=password → get_by_label("Password *") ✓
- Submit button: get_by_role("button", name="Continue", exact=True) ✓
- After login: redirects to https://apps.private.cytoreason.com/platform/customers/pyy/

CRITICAL: Navigation to BASE_URL must use wait_until="networkidle" (not domcontentloaded)
so that the React SPA's JS fires, detects the unauthenticated state, and completes the
Auth0 redirect before the caller checks the URL.
"""
from __future__ import annotations

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from src.config import settings
from src.ui.selectors import login_sel


class LoginPage:
    def __init__(self, page: Page) -> None:
        self.page = page

    async def goto(self) -> None:
        """
        Navigate to the platform.  Uses networkidle so the React SPA can fire
        and the Auth0 redirect completes before the caller checks the URL.
        """
        self.page.set_default_timeout(settings.default_timeout_ms)
        self.page.set_default_navigation_timeout(settings.navigation_timeout_ms)
        await self.page.goto(settings.base_url, wait_until="networkidle")

    async def login(self) -> None:
        """
        Fill and submit the Auth0 login form.

        Waits for the email field (handles slow SSO redirects), fills both
        fields, and clicks Continue.  Callers are responsible for verifying
        the app loaded after this returns.
        """
        await self.page.wait_for_load_state("domcontentloaded")

        email_loc = self.page.get_by_label(login_sel.username_input_label)
        pass_loc = self.page.get_by_label(login_sel.password_input_label)

        # Auth0 redirect can be slow; reload once if form doesn't appear
        try:
            await email_loc.wait_for(
                state="visible", timeout=settings.navigation_timeout_ms
            )
        except PlaywrightTimeoutError:
            await self.page.reload(wait_until="domcontentloaded")
            await email_loc.wait_for(
                state="visible", timeout=settings.navigation_timeout_ms
            )

        await email_loc.fill(settings.username)

        await pass_loc.wait_for(
            state="visible", timeout=settings.navigation_timeout_ms
        )
        await pass_loc.fill(settings.password)

        await self.page.get_by_role(
            "button", name=login_sel.continue_button_name, exact=True
        ).click()

        # Best-effort wait for redirect back to the platform (networkidle so
        # the React app fully boots before the caller asserts readiness).
        base = settings.base_url.rstrip("/")
        if base not in self.page.url:
            try:
                await self.page.wait_for_url(
                    f"**{base}/**",
                    wait_until="networkidle",
                    timeout=30_000,
                )
            except PlaywrightTimeoutError:
                pass  # Caller will surface the failure when checking readiness
