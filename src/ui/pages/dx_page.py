"""
Disease Explorer / DX page object.

URL: {base_url}/disease-explorer/differential-expression

LIVE VALIDATED (2026-03-11):
- Model picker is a <button role="combobox"> with NO aria-label.
  Must use locator("button").filter(has_text="Disease Model").first
- Analysis type toggles are <button role="radio">: Target Gene, Target Signature,
  Meta Analysis, Per Dataset.  "White Space" does NOT exist on this page.
- Filter comboboxes are Radix UI select triggers with no aria-label;
  identified by has_text of their current displayed value.
- Model picker dropdown items (no space between abbr and name):
  ASTHAsthma, CECeliac Disease, COPDChronic Obstructive Pulmonary Disease,
  CDCrohn's Disease, SSCSystemic Sclerosis, UCUlcerative Colitis
- Inventory side-nav: role=link name="Inventory"
"""
from __future__ import annotations

from playwright.async_api import Page

from src.config import settings
from src.ui.pages.base_page import BasePage
from src.ui.selectors import dx_sel, inventory_sel


class DxPage(BasePage):
    URL = f"{settings.base_url}{dx_sel.de_path}"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        # Model picker button (page-ready signal).
        # No aria-label → must use has_text filter.
        self._model_picker = page.locator("button").filter(
            has_text=dx_sel.model_picker_has_text
        ).first

    # ------------------------------------------------------------------ open
    async def open(self) -> None:
        """Navigate to the DX page; wait until the model picker is visible."""
        await self.goto_url(self.URL, self._model_picker)

    async def wait_for_model_loaded(self) -> None:
        """Wait for the model picker button to appear (confirms page rendered)."""
        await self._model_picker.wait_for(
            state="visible", timeout=settings.navigation_timeout_ms
        )

    # ---------------------------------------------------------- model picker
    async def open_model_picker(self) -> None:
        """Click the model picker to reveal the model selection dropdown."""
        await self.safe_click(self._model_picker)

    async def select_model_from_dropdown(self, has_text: str) -> None:
        """
        Click the model in the open dropdown whose text contains *has_text*.

        Parameters
        ----------
        has_text : str
            Substring of the model name, e.g. "Chronic Obstructive Pulmonary Disease"
            for COPD, or "Ulcerative Colitis" for UC.
        """
        item = self.page.locator("a, button, li").filter(has_text=has_text).first
        await self.safe_click(item)
        # Wait for the picker to update (page settling after model switch)
        await self._model_picker.wait_for(
            state="visible", timeout=settings.navigation_timeout_ms
        )

    # ------------------------------------------------------- analysis toggles
    async def select_target_gene_analysis(self) -> None:
        """Select the Target Gene analysis type (role=radio button)."""
        await self.safe_click(
            self.page.get_by_role("radio", name=dx_sel.radio_target_gene)
        )

    async def select_target_signature_analysis(self) -> None:
        """Select the Target Signature analysis type (role=radio button)."""
        await self.safe_click(
            self.page.get_by_role("radio", name=dx_sel.radio_target_signature)
        )

    # ------------------------------------------------------- filter comboboxes
    async def open_and_dismiss_combobox(self, has_text: str) -> None:
        """
        Open a filter combobox (identified by *has_text* of its current value)
        then dismiss with Escape to simulate a user browsing options.
        """
        combo = self.page.locator("button[role='combobox']").filter(
            has_text=has_text
        ).first
        await self.safe_click(combo)
        await self.page.keyboard.press("Escape")

    # --------------------------------------------------------- inventory nav
    async def navigate_to_inventory(self) -> None:
        """Click the Inventory side-nav link."""
        link = self.page.get_by_role("link", name=inventory_sel.inventory_link_name)
        await self.safe_click(link)
