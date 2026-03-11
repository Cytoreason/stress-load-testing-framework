"""
Disease Explorer / DX page object.

URL: {base_url}/disease-explorer/differential-expression

Validated interactions:
- Navigate to the Differential Expression view
- Wait for the ASTH disease model combobox (page ready signal)
- Switch between disease models (ASTH, COPD, UC)
- Select White Space / Target Signature analysis types
- Interact with filter comboboxes (bronchus, disease vs control, etc.)
- Navigate to Inventory from side-nav
"""
from __future__ import annotations

import re

from playwright.async_api import Page

from src.config import settings
from src.ui.pages.base_page import BasePage
from src.ui.selectors import dx_sel, inventory_sel


class DxPage(BasePage):
    URL = f"{settings.base_url}{dx_sel.de_path}"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._asth_model_combo = page.get_by_role(
            "combobox", name=dx_sel.asth_model_combobox
        )

    # ------------------------------------------------------------------ open
    async def open(self) -> None:
        """Navigate to /disease-explorer/differential-expression."""
        await self.goto_url(self.URL, self._asth_model_combo)

    # ---------------------------------------------------------- model switcher
    async def open_disease_models_menu(self) -> None:
        btn = self.page.get_by_role("button", name=dx_sel.disease_models_button)
        await self.safe_click(btn)

    async def select_disease_model_by_link_prefix(self, prefix: str) -> None:
        """Click the first nav link whose text starts with *prefix*."""
        link = self.page.get_by_role("link", name=re.compile(rf"^{re.escape(prefix)}\b"))
        await self.safe_click(link)

    async def wait_for_model_combobox(self, name_pattern: str) -> None:
        combo = self.page.get_by_role("combobox", name=re.compile(name_pattern))
        await combo.wait_for(state="visible", timeout=settings.navigation_timeout_ms)

    # ------------------------------------------------------- analysis controls
    async def select_white_space_analysis(self) -> None:
        radio = self.page.get_by_role("radio", name=dx_sel.radio_white_space)
        await self.safe_click(radio)

    async def select_target_signature_analysis(self) -> None:
        radio = self.page.get_by_role("radio", name=dx_sel.radio_target_signature)
        await self.safe_click(radio)

    # ------------------------------------------------------- filter comboboxes
    async def open_and_dismiss_combobox(self, combobox_name: str) -> None:
        """Open a filter combobox dropdown then dismiss it (simulates user browsing)."""
        combo = self.page.get_by_role("combobox", name=combobox_name)
        await self.safe_click(combo)
        await self.page.keyboard.press("Escape")

    # --------------------------------------------------------- inventory nav
    async def navigate_to_inventory(self) -> None:
        link = self.page.get_by_role("link", name=inventory_sel.inventory_link_name)
        await self.safe_click(link)
