"""
CytoPedia page object.

URL: {base_url}/cytopedia

LIVE VALIDATED (2026-03-11):
- Search textbox: matched by placeholder via accessible name ("Search terms by title or description")
- Entities button: get_by_role("button", name="Entities", exact=True).first  ✓
- Cell Entities: get_by_role("button", name="Cell Entities") ✓
  (rendered as a <button> in an expandable result list, NOT an <a> link)
- CytoPedia button list on Entities tab: Entities, Evidences, Methods, Concepts, QCM,
  followed by result items like "Cell Entities", "View All N Results"
"""
from __future__ import annotations

from playwright.async_api import Page

from src.config import settings
from src.ui.pages.base_page import BasePage
from src.ui.selectors import cytopedia_sel


class CytopediaPage(BasePage):
    URL = f"{settings.base_url}{cytopedia_sel.cytopedia_path}"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._search = page.get_by_role(
            "textbox", name=cytopedia_sel.search_accessible_name
        )

    # ------------------------------------------------------------------ open
    async def open(self) -> None:
        await self.goto_url(self.URL, self._search)

    # ------------------------------------------------------------- categories
    async def filter_by_entities(self) -> None:
        btn = self.page.get_by_role(
            "button", name=cytopedia_sel.entities_button, exact=True
        ).first
        await self.safe_click(btn)

    # ----------------------------------------------------------------- search
    async def search(self, query: str) -> None:
        await self.fill_and_wait(self._search, query)

    # ---------------------------------------------------------- result click
    async def open_cell_entities(self) -> None:
        link = self.page.get_by_role("button", name=cytopedia_sel.cell_entities_link)
        await self.safe_click(link)
