"""
Inventory page object.

The Inventory view is a sub-page inside the Disease Explorer.
Accessed via the "Inventory" side-nav link after a disease model is loaded.

Validated interactions:
- Wait for the Disease Biology accordion/button (page ready signal)
- Click "Disease Biology" to expand category
- Navigate individual inventory items by link text
"""
from __future__ import annotations

from playwright.async_api import Page

from src.config import settings
from src.ui.pages.base_page import BasePage
from src.ui.selectors import inventory_sel


class InventoryPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._disease_biology_btn = page.get_by_role(
            "button", name=inventory_sel.disease_biology_button
        )

    # -------------------------------------------------- readiness verification
    async def wait_until_ready(self) -> None:
        """Wait for the Disease Biology button – signals inventory has rendered."""
        await self._disease_biology_btn.wait_for(
            state="visible", timeout=settings.navigation_timeout_ms
        )

    # ------------------------------------------------------- category controls
    async def expand_disease_biology(self) -> None:
        await self.safe_click(self._disease_biology_btn)

    # ---------------------------------------------------------- item navigation
    async def open_item(self, item_name: str) -> None:
        link = self.page.get_by_role("link", name=item_name)
        await self.safe_click(link)
        # Wait for content to load (no dedicated signal – DOM settle suffices)
        await self.page.wait_for_load_state("domcontentloaded")

    async def open_target_expression(self) -> None:
        await self.open_item(inventory_sel.item_target_expression)

    async def open_target_regulation(self) -> None:
        await self.open_item(inventory_sel.item_target_regulation)

    async def open_cell_abundance(self) -> None:
        await self.open_item(inventory_sel.item_cell_abundance)

    async def open_disease_severity(self) -> None:
        await self.open_item(inventory_sel.item_disease_severity)

    async def open_soc_treatment(self) -> None:
        await self.open_item(inventory_sel.item_soc_treatment)
