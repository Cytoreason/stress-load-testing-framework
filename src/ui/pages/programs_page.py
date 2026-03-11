"""
Programs / Projects page object.

URL: {base_url}/programs

Validated interactions:
- Navigate to the Programs landing page
- Wait for the search textbox to appear (page ready signal)
- Filter by "My Projects" / "All Projects"
- Type a search query and clear it
"""
from __future__ import annotations

from playwright.async_api import Page

from src.config import settings
from src.ui.pages.base_page import BasePage
from src.ui.selectors import programs_sel


class ProgramsPage(BasePage):
    URL = f"{settings.base_url}/programs"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        # Primary ready-locator – visible after the page fully renders
        self._search = page.get_by_role(
            "textbox", name=programs_sel.search_accessible_name
        )

    # ------------------------------------------------------------------ open
    async def open(self) -> None:
        """Navigate to /programs and wait until the page is interactive."""
        await self.goto_url(self.URL, self._search)

    # ----------------------------------------------------------------- search
    async def search(self, query: str) -> None:
        await self.fill_and_wait(self._search, query)

    async def clear_search(self) -> None:
        await self.fill_and_wait(self._search, "")

    # -------------------------------------------------------------- filtering
    async def filter_my_projects(self) -> None:
        btn = self.page.get_by_role("button", name=programs_sel.my_projects_button)
        await self.safe_click(btn)

    async def filter_all_projects(self) -> None:
        btn = self.page.get_by_role("button", name=programs_sel.all_projects_button)
        await self.safe_click(btn)
