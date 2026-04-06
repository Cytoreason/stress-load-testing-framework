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
async def test_dx_page_model_picker_present(page: Page) -> None:
    """Model picker button (has_text 'Disease Model') must be visible on the DX page.

    LIVE VALIDATED (2026-03-11): The Radix UI combobox has NO aria-label;
    selector strategy is locator('button').filter(has_text='Disease Model').first.
    """
    dx = DxPage(page)
    await dx.open()
    # Use the same strategy as DxPage._model_picker
    picker = page.locator("button").filter(has_text=dx_sel.model_picker_has_text).first
    await expect(picker).to_be_visible(timeout=settings.navigation_timeout_ms)


@pytest.mark.smoke
@pytest.mark.selector
@pytest.mark.ui
async def test_dx_page_analysis_radios_present(page: Page) -> None:
    """Target Gene and Target Signature radio buttons must be visible on the DX page.

    LIVE VALIDATED (2026-03-11): 'White Space' does NOT exist.
    Real toggles are: Target Gene, Target Signature, Meta Analysis, Per Dataset.
    """
    dx = DxPage(page)
    await dx.open()
    await expect(
        page.get_by_role("radio", name=dx_sel.radio_target_gene)
    ).to_be_visible(timeout=settings.default_timeout_ms)
    await expect(
        page.get_by_role("radio", name=dx_sel.radio_target_signature)
    ).to_be_visible(timeout=settings.default_timeout_ms)


@pytest.mark.smoke
@pytest.mark.selector
@pytest.mark.ui
async def test_dx_page_filter_comboboxes_present(page: Page) -> None:
    """Tissue and comparison filter comboboxes must be visible on the DX page."""
    dx = DxPage(page)
    await dx.open()
    tissue_combo = page.locator("button[role='combobox']").filter(
        has_text=dx_sel.combobox_tissue_has_text
    ).first
    comparison_combo = page.locator("button[role='combobox']").filter(
        has_text=dx_sel.combobox_comparison_has_text
    ).first
    await expect(tissue_combo).to_be_visible(timeout=settings.default_timeout_ms)
    await expect(comparison_combo).to_be_visible(timeout=settings.default_timeout_ms)


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
    """Key inventory items must be present after expanding Disease Biology.

    LIVE VALIDATED (2026-03-11): Items appear as both links and buttons (Radix
    collapsible pattern). Selector uses locator filter with has_text.
    """
    dx = DxPage(page)
    await dx.open()
    await dx.navigate_to_inventory()
    inv = InventoryPage(page)
    await inv.wait_until_ready()
    await inv.expand_disease_biology()

    for item_name in [
        inventory_sel.item_target_expression,
        inventory_sel.item_target_regulation,
        inventory_sel.item_cell_abundance,
        inventory_sel.item_target_cell_assoc,
        inventory_sel.item_target_pathway_assoc,
    ]:
        item = page.locator("a, button").filter(has_text=item_name).first
        await expect(item).to_be_visible(timeout=settings.default_timeout_ms)
