"""
Disease Explorer / DX workflow journey.

LIVE VALIDATED (2026-03-11) against staging platform.

Simulates an analyst exploring the Differential Expression view:
1. Load the ASTH disease model (navigate to DX page)
2. Select Target Gene → Target Signature analysis type
3. Browse tissue and comparison filter comboboxes
4. Switch to COPD model via the model picker dropdown
5. Navigate to Inventory and open a Disease Biology item (COPD)
6. Return to DX and switch to UC model
7. Navigate to Inventory and open a Disease Biology item (UC)

Locust event names emitted:
  - UI_Open_DX_Differential_Expression_Page
  - UI_Load_DX_Disease_Model_ASTH
  - UI_Select_DX_Target_Gene_Analysis
  - UI_Select_DX_Target_Signature_Analysis
  - UI_Browse_DX_Filter_Tissue
  - UI_Browse_DX_Filter_Comparison
  - UI_Switch_DX_Disease_Model_COPD
  - UI_Navigate_To_Inventory_Page_COPD
  - UI_Open_Inventory_Item_Target_Expression_COPD
  - UI_Switch_DX_Disease_Model_UC
  - UI_Navigate_To_Inventory_Page_UC
  - UI_Open_Inventory_Item_Target_Expression_UC
"""
from __future__ import annotations

from locust_plugins.users.playwright import event
from playwright.async_api import Page

from src.config import settings
from src.ui.pages.dx_page import DxPage
from src.ui.pages.inventory_page import InventoryPage
from src.ui.selectors import dx_sel


async def run_dx_journey(page: Page, user) -> None:
    """
    Execute the full DX workflow journey.

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

    async with event(user, "UI_Load_DX_Disease_Model_ASTH"):
        # Model picker is the page-ready signal from dx.open().
        # Recorded again here to capture the model render latency.
        await dx.wait_for_model_loaded()

    async with event(user, "UI_Select_DX_Target_Gene_Analysis"):
        await dx.select_target_gene_analysis()

    async with event(user, "UI_Select_DX_Target_Signature_Analysis"):
        await dx.select_target_signature_analysis()

    # Browse filter comboboxes (open and dismiss – simulates user scanning)
    async with event(user, "UI_Browse_DX_Filter_Tissue"):
        await dx.open_and_dismiss_combobox(dx_sel.combobox_tissue_has_text)

    async with event(user, "UI_Browse_DX_Filter_Comparison"):
        await dx.open_and_dismiss_combobox(dx_sel.combobox_comparison_has_text)

    # Switch to COPD model
    async with event(user, "UI_Switch_DX_Disease_Model_COPD"):
        await dx.open_model_picker()
        await dx.select_model_from_dropdown(dx_sel.copd_dropdown_has_text)

    async with event(user, "UI_Navigate_To_Inventory_Page_COPD"):
        await dx.navigate_to_inventory()
        await inv.wait_until_ready()

    async with event(user, "UI_Open_Inventory_Item_Target_Expression_COPD"):
        await inv.expand_disease_biology()
        await inv.open_target_expression()

    # Navigate back to DX and switch to UC model
    async with event(user, "UI_Switch_DX_Disease_Model_UC"):
        await page.goto(DxPage.URL, wait_until="domcontentloaded")
        await dx.wait_for_model_loaded()
        await dx.open_model_picker()
        await dx.select_model_from_dropdown(dx_sel.uc_dropdown_has_text)

    async with event(user, "UI_Navigate_To_Inventory_Page_UC"):
        await dx.navigate_to_inventory()
        await inv.wait_until_ready()

    async with event(user, "UI_Open_Inventory_Item_Target_Expression_UC"):
        await inv.expand_disease_biology()
        await inv.open_target_expression()
