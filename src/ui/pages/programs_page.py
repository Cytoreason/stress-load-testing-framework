"""
Programs / Projects page object.

URL: {base_url}/programs

URL-FIRST DESIGN — same principle as DX/Inventory pages:
The search textbox and filter buttons are API-loaded (appear only after the
Projects API responds).  open() confirms the URL only.  Each interaction
method polls for its own element in 20 s chunks so auth-refresh redirects
(which fire mid-wait and cannot be caught by a plain wait_for) are detected
and recovered before each chunk times out.
"""
from __future__ import annotations

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from src.config import settings
from src.ui.pages.base_page import BasePage
from src.ui.selectors import programs_sel


class ProgramsPage(BasePage):
    URL = f"{settings.base_url}/programs"

    _INTERACT_TIMEOUT_MS = 90_000   # total budget per interaction event
    _CHUNK_MS = 20_000              # poll interval — large enough for slow API,
                                    # small enough to detect mid-wait auth redirects

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._search = page.get_by_role(
            "textbox", name=programs_sel.search_accessible_name
        )

    # ------------------------------------------------------------------ open
    async def open(self) -> None:
        """Navigate to /programs — URL match only, no element wait."""
        await self.goto_url(self.URL, retries=1)

    # ---------------------------------------------------------------- helpers
    async def _ensure_on_programs_page(self) -> None:
        """Re-navigate URL-only if an auth refresh redirected us away."""
        await self._recover_auth_if_needed()
        if "/programs" not in self.page.url:
            await self.goto_url(self.URL, retries=1)

    async def _poll_click(self, locator_name: str) -> None:
        """Poll for a named button in chunks, recovering auth redirects mid-wait."""
        remaining_ms = self._INTERACT_TIMEOUT_MS
        while remaining_ms > 0:
            btn = self.page.get_by_role("button", name=locator_name)
            try:
                await btn.wait_for(
                    state="visible", timeout=min(self._CHUNK_MS, remaining_ms)
                )
                await btn.click()
                return
            except (PlaywrightTimeoutError, PlaywrightError):
                remaining_ms -= self._CHUNK_MS
                await self._recover_auth_if_needed()
                if "/programs" not in self.page.url:
                    await self.goto_url(self.URL, retries=1)
        raise PlaywrightTimeoutError(
            f"Button '{locator_name}' not visible after {self._INTERACT_TIMEOUT_MS}ms"
        )

    async def _poll_fill(self, text: str) -> None:
        """Poll for the search textbox in chunks, recovering auth redirects mid-wait."""
        remaining_ms = self._INTERACT_TIMEOUT_MS
        while remaining_ms > 0:
            try:
                await self._search.wait_for(
                    state="visible", timeout=min(self._CHUNK_MS, remaining_ms)
                )
                await self._search.fill(text)
                await self.page.wait_for_timeout(300)
                return
            except (PlaywrightTimeoutError, PlaywrightError):
                remaining_ms -= self._CHUNK_MS
                await self._recover_auth_if_needed()
                if "/programs" not in self.page.url:
                    await self.goto_url(self.URL, retries=1)
        raise PlaywrightTimeoutError(
            f"Search textbox not visible after {self._INTERACT_TIMEOUT_MS}ms"
        )

    # ----------------------------------------------------------------- search
    async def search(self, query: str) -> None:
        await self._ensure_on_programs_page()
        await self._poll_fill(query)

    async def clear_search(self) -> None:
        await self._ensure_on_programs_page()
        await self._poll_fill("")

    # -------------------------------------------------------------- filtering
    async def filter_my_projects(self) -> None:
        await self._ensure_on_programs_page()
        await self._poll_click(programs_sel.my_projects_button)

    async def filter_all_projects(self) -> None:
        await self._ensure_on_programs_page()
        await self._poll_click(programs_sel.all_projects_button)
