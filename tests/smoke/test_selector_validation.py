"""
Selector validation smoke tests.

Each test navigates to the relevant page and asserts that the selector used
in the load framework is still present in the live DOM.

Run these before every load/stress run:
    pytest -m selector -v

A failing selector test means the corresponding selector in
src/ui/selectors.py must be updated before the load run.

Marks: smoke, selector, ui
"""
from __future__ import annotations

import pytest
from playwright.async_api import Page, expect

from src.config import settings
from src.ui.pages.programs_page import ProgramsPage
from src.ui.pages.cytopedia_page import CytopediaPage
from src.ui.pages.dx_page import DxPage
from src.ui.pages.inventory_page import InventoryPage
from src.ui.selectors import (
    cytopedia_sel,
    dx_sel,
    inventory_sel,
    programs_sel,
    ready_sel,
)


# ---------------------------------------------------------------------------
# Programs page selectors
# ---------------------------------------------------------------------------

@pytest.mark.smoke
@pytest.mark.selector
@pytest.mark.ui
async def test_programs_page_search_box_present(page: Page) -> None:
    """Search textbox on /programs must be visible."""
    pp = ProgramsPage(page)
    await pp.open()
    search = page.get_by_role("textbox", name=programs_sel.search_accessible_name)
    await expect(search).to_be_visible(timeout=settings.default_timeout_ms)


@pytest.mark.smoke
@pytest.mark.selector
@pytest.mark.ui
async def test_programs_page_filter_buttons_present(page: Page) -> None:
    """My Projects and All Projects buttons must be visible."""
    pp = ProgramsPage(page)
    await pp.open()
    await expect(
        page.get_by_role("button", name=programs_sel.my_projects_button)
    ).to_be_visible()
    await expect(
        page.get_by_role("button", name=programs_sel.all_projects_button)
    ).to_be_visible()


# ---------------------------------------------------------------------------
# CytoPedia page selectors
# ---------------------------------------------------------------------------

@pytest.mark.smoke
@pytest.mark.selector
@pytest.mark.ui
async def test_cytopedia_page_search_box_present(page: Page) -> None:
    """Search textbox on /cytopedia must be visible."""
    cp = CytopediaPage(page)
    await cp.open()
    search = page.get_by_role("textbox", name=cytopedia_sel.search_accessible_name)
    await expect(search).to_be_visible(timeout=settings.default_timeout_ms)


@pytest.mark.smoke
@pytest.mark.selector
@pytest.mark.ui
async def test_cytopedia_entities_button_present(page: Page) -> None:
    """Entities filter button on /cytopedia must be visible."""
    cp = CytopediaPage(page)
    await cp.open()
    btn = page.get_by_role("button", name=cytopedia_sel.entities_button, exact=True).first
    await expect(btn).to_be_visible(timeout=settings.default_timeout_ms)


# ---------------------------------------------------------------------------
# Disease Explorer / DX page selectors
# ---------------------------------------------------------------------------

@pytest.mark.smoke
@pytest.mark.selector
@pytest.mark.ui
async def test_dx_page_asth_model_combobox_present(page: Page) -> None:
    """ASTH model combobox on /disease-explorer/differential-expression must be visible."""
    dx = DxPage(page)
    await dx.open()
    combo = page.get_by_role("combobox", name=dx_sel.asth_model_combobox)
    await expect(combo).to_be_visible(timeout=settings.navigation_timeout_ms)


@pytest.mark.smoke
@pytest.mark.selector
@pytest.mark.ui
async def test_dx_page_analysis_radios_present(page: Page) -> None:
    """White Space and Target Signature radio buttons must be visible."""
    dx = DxPage(page)
    await dx.open()
    await expect(
        page.get_by_role("radio", name=dx_sel.radio_white_space)
    ).to_be_visible(timeout=settings.default_timeout_ms)
    await expect(
        page.get_by_role("radio", name=dx_sel.radio_target_signature)
    ).to_be_visible(timeout=settings.default_timeout_ms)


# ---------------------------------------------------------------------------
# Inventory page selectors
# ---------------------------------------------------------------------------

@pytest.mark.smoke
@pytest.mark.selector
@pytest.mark.ui
async def test_inventory_page_disease_biology_button_present(page: Page) -> None:
    """
    Disease Biology button must appear after navigating to Inventory from DX.
    """
    dx = DxPage(page)
    await dx.open()
    await dx.navigate_to_inventory()

    inv = InventoryPage(page)
    await inv.wait_until_ready()

    await expect(
        page.get_by_role("button", name=inventory_sel.disease_biology_button)
    ).to_be_visible(timeout=settings.navigation_timeout_ms)


@pytest.mark.smoke
@pytest.mark.selector
@pytest.mark.ui
async def test_inventory_page_item_links_present(page: Page) -> None:
    """Key inventory item links must be present after opening Inventory."""
    dx = DxPage(page)
    await dx.open()
    await dx.navigate_to_inventory()
    inv = InventoryPage(page)
    await inv.wait_until_ready()
    await inv.expand_disease_biology()

    for item_name in [
        inventory_sel.item_target_expression,
        inventory_sel.item_target_regulation,
    ]:
        await expect(
            page.get_by_role("link", name=item_name)
        ).to_be_visible(timeout=settings.default_timeout_ms)
