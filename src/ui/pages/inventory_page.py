"""
Inventory page object.

URL: /disease-explorer/model-inventory/<model-slug>
Accessed via the "Inventory" side-nav link after a disease model is loaded.

LIVE VALIDATED (2026-03-11):
- Disease Biology button is present and works as the page-ready signal.
- Clicking Disease Biology expands a list of inventory items.
- Items appear as BOTH links and buttons in the DOM (Radix collapsible).
- Item text format: "N.Item Name" (NO spaces around the dot).
- Validated items for ASTH Disease Biology (6 items):
    1.Target Expression in Disease
    2.Target Regulation in Disease
    3.Differential Cell Abundance in Disease
    4.Target-Cell Association
    5.Target-Pathway Association
    6.Differential expression across diseases
- Items 7 and 8 from prior assumptions do NOT exist.
"""
from __future__ import annotations

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from src.config import settings
from src.ui.pages.base_page import BasePage
from src.ui.selectors import inventory_sel


class InventoryPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._disease_biology_btn = self.page.get_by_role(
            "button", name=inventory_sel.disease_biology_button
        )

    # -------------------------------------------------- readiness
    async def wait_until_ready(self) -> None:
        """Confirm the inventory page has arrived (URL match only).

        Disease Biology is API-loaded and must not block navigation — it is
        waited on inside ``expand_disease_biology()`` where it is actually used.
        """
        timeout_ms = max(settings.navigation_timeout_ms, 60_000)
        await self._recover_auth_if_needed()
        await self.page.wait_for_url(
            "**/disease-explorer/model-inventory/**",
            wait_until="domcontentloaded",
            timeout=timeout_ms,
        )

    # ------------------------------------------------------- category
    async def expand_disease_biology(self) -> None:
        """Click Disease Biology to expand its inventory item list.

        Captures the inventory URL at entry so that auth refreshes mid-wait
        can be recovered by re-navigating back to the same page.
        """
        timeout_ms = max(settings.navigation_timeout_ms, 120_000)
        inventory_url = self.page.url  # capture before any possible redirect
        remaining_ms = timeout_ms
        chunk_ms = 8_000
        while remaining_ms > 0:
            try:
                await self._disease_biology_btn.wait_for(
                    state="visible", timeout=min(chunk_ms, remaining_ms)
                )
                break  # visible — proceed to click
            except PlaywrightTimeoutError:
                remaining_ms -= chunk_ms
                await self._recover_auth_if_needed()
                if "disease-explorer/model-inventory" not in self.page.url:
                    await self.page.goto(
                        inventory_url, wait_until="domcontentloaded", timeout=30_000
                    )
                if remaining_ms <= 0:
                    raise PlaywrightTimeoutError(
                        f"Disease Biology button not visible after {timeout_ms}ms"
                    )
        await self._disease_biology_btn.click()
        # Brief pause for the animation / DOM insertion to settle
        await self.page.wait_for_timeout(400)
        await self.page.locator("a, button").filter(
            has_text=inventory_sel.item_target_expression
        ).first.wait_for(state="visible", timeout=timeout_ms)

    # ---------------------------------------------------------- item navigation
    async def open_item_by_partial_text(self, partial_text: str) -> None:
        """
        Click the first inventory item whose text contains *partial_text*.

        Uses has_text filter because items appear as both links and buttons;
        the filter approach is robust to role ambiguity.
        """
        item = self.page.locator("a, button").filter(has_text=partial_text).first
        await item.wait_for(
            state="visible", timeout=max(settings.navigation_timeout_ms, 60_000)
        )
        await item.scroll_into_view_if_needed()
        await self.safe_click(item)
        await self.page.wait_for_load_state("domcontentloaded")

    async def open_target_expression(self) -> None:
        await self.open_item_by_partial_text(inventory_sel.item_target_expression)

    async def open_target_regulation(self) -> None:
        await self.open_item_by_partial_text(inventory_sel.item_target_regulation)

    async def open_cell_abundance(self) -> None:
        await self.open_item_by_partial_text(inventory_sel.item_cell_abundance)

    async def open_target_cell_assoc(self) -> None:
        await self.open_item_by_partial_text(inventory_sel.item_target_cell_assoc)

    async def open_target_pathway_assoc(self) -> None:
        await self.open_item_by_partial_text(inventory_sel.item_target_pathway_assoc)

    async def open_diff_expression_diseases(self) -> None:
        await self.open_item_by_partial_text(inventory_sel.item_diff_expression_diseases)
