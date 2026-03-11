"""
CytoPedia journey.

Simulates a user browsing the CytoPedia knowledge base:
1. Navigate to /cytopedia
2. Filter by "Entities" category
3. Search for "cell"
4. Open the "Cell Entities" category result

Locust event names emitted:
  - UI_Open_CytoPedia_Page
  - UI_Filter_CytoPedia_Entities_Category
  - UI_Search_CytoPedia_Terms
  - UI_Open_CytoPedia_Cell_Entities
"""
from __future__ import annotations

from locust_plugins.users.playwright import event
from playwright.async_api import Page

from src.ui.pages.cytopedia_page import CytopediaPage


async def run_cytopedia_journey(page: Page, user) -> None:
    """
    Execute the CytoPedia browsing journey.

    Parameters
    ----------
    page : playwright.async_api.Page
        The Playwright page bound to the current Locust user session.
    user : PlaywrightUser
        Locust user instance; required for ``event()`` metric reporting.
    """
    cp = CytopediaPage(page)

    async with event(user, "UI_Open_CytoPedia_Page"):
        await cp.open()

    async with event(user, "UI_Filter_CytoPedia_Entities_Category"):
        await cp.filter_by_entities()

    async with event(user, "UI_Search_CytoPedia_Terms"):
        await cp.search("cell")

    async with event(user, "UI_Open_CytoPedia_Cell_Entities"):
        await cp.open_cell_entities()
