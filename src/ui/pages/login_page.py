from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from src.config import settings
from src.ui.selectors import login_sel, ready_sel


class LoginPage:
    def __init__(self, page: Page):
        self.page = page

    async def goto(self) -> None:
        self.page.set_default_timeout(settings.default_timeout_ms)
        self.page.set_default_navigation_timeout(settings.navigation_timeout_ms)
        await self.page.goto(settings.base_url, wait_until="domcontentloaded")

    async def login(self) -> None:
        # Prefer label/role-based locators (stable under UI changes)
        await self.page.wait_for_load_state("domcontentloaded")
        username = self.page.get_by_label(login_sel.username_input_label)
        password = self.page.get_by_label(login_sel.password_input_label)
        try:
            await username.wait_for(
                state="visible", timeout=settings.navigation_timeout_ms
            )
        except Exception:
            await self.page.reload(wait_until="domcontentloaded")
            await username.wait_for(
                state="visible", timeout=settings.navigation_timeout_ms
            )
        await username.fill(settings.username)
        await password.wait_for(
            state="visible", timeout=settings.navigation_timeout_ms
        )
        await password.fill(settings.password)
        await self.page.get_by_role(
            "button", name=login_sel.continue_button_name, exact=True
        ).click()

        # Do not hard-block on app readiness here; caller will verify it.
        base_url = settings.base_url.strip("/")
        if base_url not in self.page.url:
            try:
                await self.page.wait_for_url(
                    f"**{base_url}/**",
                    wait_until="domcontentloaded",
                    timeout=15000,
                )
            except PlaywrightTimeoutError:
                return
