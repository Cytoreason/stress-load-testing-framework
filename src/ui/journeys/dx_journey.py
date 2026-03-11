"""
Disease Explorer / DX workflow journey.

Simulates an analyst exploring the Differential Expression view:
1. Load the ASTH disease model
2. Select White Space → Target Signature analysis
3. Browse filter comboboxes
4. Switch disease models (ASTH → COPD → UC) via the side-nav
5. Re-visit the Inventory items for each subsequent model

Locust event names emitted:
  - UI_Open_DX_Differential_Expression_Page
  - UI_Load_DX_Disease_Model_ASTH
  - UI_Select_DX_White_Space_Analysis
  - UI_Select_DX_Target_Signature_Analysis
  - UI_Browse_DX_Filter_Bronchus
  - UI_Browse_DX_Filter_Disease_Vs_Control
  - UI_Browse_DX_Filter_Fluticasone
  - UI_Browse_DX_Filter_Week1_500ug
  - UI_Switch_DX_Disease_Model_COPD
  - UI_Open_Inventory_Item_Target_Expression_COPD
  - UI_Switch_DX_Disease_Model_UC
  - UI_Open_Inventory_Item_Target_Expression_UC
"""
from __future__ import annotations

from locust_plugins.users.playwright import event
from playwright.async_api import Page

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
        # The ASTH model combobox is the page-ready signal from dx.open(),
        # but we record it explicitly to capture model render time.
        await dx._asth_model_combo.wait_for(state="visible")

    async with event(user, "UI_Select_DX_White_Space_Analysis"):
        await dx.select_white_space_analysis()

    async with event(user, "UI_Select_DX_Target_Signature_Analysis"):
        await dx.select_target_signature_analysis()

    # Browse filter comboboxes without changing values (user scanning UI)
    async with event(user, "UI_Browse_DX_Filter_Bronchus"):
        await dx.open_and_dismiss_combobox(dx_sel.combobox_bronchus)

    async with event(user, "UI_Browse_DX_Filter_Disease_Vs_Control"):
        await dx.open_and_dismiss_combobox(dx_sel.combobox_disease_vs_control)

    async with event(user, "UI_Browse_DX_Filter_Fluticasone"):
        await dx.open_and_dismiss_combobox(dx_sel.combobox_fluticasone)

    async with event(user, "UI_Browse_DX_Filter_Week1_500ug"):
        await dx.open_and_dismiss_combobox(dx_sel.combobox_week1_500ug)

    # Switch to COPD model
    async with event(user, "UI_Switch_DX_Disease_Model_COPD"):
        await dx.open_disease_models_menu()
        await dx.select_disease_model_by_link_prefix(dx_sel.copd_model_link_prefix)
        await dx.wait_for_model_combobox("COPD Disease Model")

    async with event(user, "UI_Navigate_To_Inventory_Page_COPD"):
        await dx.navigate_to_inventory()
        await inv.wait_until_ready()

    async with event(user, "UI_Open_Inventory_Item_Target_Expression_COPD"):
        await inv.open_target_expression()

    # Switch to UC model
    async with event(user, "UI_Switch_DX_Disease_Model_UC"):
        await dx.open_disease_models_menu()
        await dx.select_disease_model_by_link_prefix(dx_sel.uc_model_link_prefix)
        await dx.wait_for_model_combobox("UC Disease Model")

    async with event(user, "UI_Navigate_To_Inventory_Page_UC"):
        await dx.navigate_to_inventory()
        await inv.wait_until_ready()

    async with event(user, "UI_Open_Inventory_Item_Target_Expression_UC"):
        await inv.open_target_expression()
