"""
Inventory journey.

LIVE VALIDATED (2026-03-11) against staging platform.

Navigates through the Disease Explorer to reach the Inventory view for the
ASTH disease model, expands the Disease Biology category, and browses items.

Confirmed items for ASTH Disease Biology (6 items exist, items 7/8 do not):
  1.Target Expression in Disease
  2.Target Regulation in Disease
  3.Differential Cell Abundance in Disease
  4.Target-Cell Association
  5.Target-Pathway Association
  6.Differential expression across diseases

Locust event names emitted:
  - UI_Open_DX_Differential_Expression_Page
  - UI_Navigate_To_Inventory_Page
  - UI_Expand_Inventory_Disease_Biology
  - UI_Open_Inventory_Item_Target_Expression
  - UI_Open_Inventory_Item_Target_Regulation
  - UI_Open_Inventory_Item_Cell_Abundance
  - UI_Open_Inventory_Item_Target_Cell_Association
  - UI_Open_Inventory_Item_Target_Pathway_Association
"""
from __future__ import annotations

from locust_plugins.users.playwright import event
from playwright.async_api import Page

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

    async with event(user, "UI_Open_Inventory_Item_Target_Cell_Association"):
        await inv.open_target_cell_assoc()

    async with event(user, "UI_Open_Inventory_Item_Target_Pathway_Association"):
        await inv.open_target_pathway_assoc()
