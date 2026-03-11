"""
Inventory journey.

Navigates through the Disease Explorer to reach the Inventory view for the
ASTH disease model, then browses several inventory items.

Locust event names emitted:
  - UI_Open_DX_Differential_Expression_Page
  - UI_Navigate_To_Inventory_Page
  - UI_Expand_Inventory_Disease_Biology
  - UI_Open_Inventory_Item_Target_Expression
  - UI_Open_Inventory_Item_Target_Regulation
  - UI_Open_Inventory_Item_Cell_Abundance
  - UI_Open_Inventory_Item_Disease_Severity
  - UI_Open_Inventory_Item_SOC_Treatment
"""
from __future__ import annotations

from locust_plugins.users.playwright import event
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from src.ui.pages.dx_page import DxPage
from src.ui.pages.inventory_page import InventoryPage


async def run_inventory_journey(page: Page, user) -> None:
    """
    Execute the Inventory page journey.

    Parameters
    ----------
    page : playwright.async_api.Page
        The Playwright page bound to the current Locust user session.
    user : PlaywrightUser
        Locust user instance; required for ``event()`` metric reporting.
    """
    dx = DxPage(page)
    inv = InventoryPage(page)

    async with event(user, "UI_Open_DX_Differential_Expression_Page"):
        await dx.open()

    async with event(user, "UI_Navigate_To_Inventory_Page"):
        await dx.navigate_to_inventory()
        await inv.wait_until_ready()

    async with event(user, "UI_Expand_Inventory_Disease_Biology"):
        await inv.expand_disease_biology()

    async with event(user, "UI_Open_Inventory_Item_Target_Expression"):
        await inv.open_target_expression()

    async with event(user, "UI_Open_Inventory_Item_Target_Regulation"):
        await inv.open_target_regulation()

    async with event(user, "UI_Open_Inventory_Item_Cell_Abundance"):
        await inv.open_cell_abundance()

    async with event(user, "UI_Open_Inventory_Item_Disease_Severity"):
        await inv.open_disease_severity()

    async with event(user, "UI_Open_Inventory_Item_SOC_Treatment"):
        await inv.open_soc_treatment()
