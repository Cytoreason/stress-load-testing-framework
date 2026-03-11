"""
Journey smoke tests.

Run each journey end-to-end as a Pytest test to validate:
1. All page navigations succeed.
2. All key selectors are found.
3. All expected state transitions occur.

These are the pre-flight validation tests that MUST pass before starting
any Locust load or stress run.

Usage:
    # Run all journey smoke tests
    pytest tests/journeys/ -m smoke -v

    # Run a specific journey
    pytest tests/journeys/test_journeys_smoke.py::test_programs_journey_smoke -v
"""
from __future__ import annotations

import pytest
from playwright.async_api import Page

from src.ui.journeys.cytopedia_journey import run_cytopedia_journey
from src.ui.journeys.dx_journey import run_dx_journey
from src.ui.journeys.inventory_journey import run_inventory_journey
from src.ui.journeys.programs_journey import run_programs_journey


class _FakeUser:
    """
    Minimal Locust user stub for Pytest runs.

    Replaces ``event(user, name)`` with a no-op async context manager so the
    journey functions execute identically but without needing a running Locust
    environment.
    """

    class _NoOpEvent:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            pass

    def __getattr__(self, _name: str):
        # Return a callable that ignores args and returns a no-op context manager
        return lambda *args, **kwargs: self._NoOpEvent()


# The journey functions import ``event`` from locust_plugins, so we need to
# patch it at the module level in each journey module during smoke runs.
# Alternatively – and more cleanly – we pass the _FakeUser whose event()
# attribute returns a no-op context manager.
#
# NOTE: The journey functions call ``event(user, "UI_...")`` where ``event`` is
# imported from locust_plugins.  In smoke test context we still import from
# locust_plugins, but since no Locust environment is running the events are
# simply discarded.  The important behaviour (navigation, waits, assertions)
# is fully exercised.


@pytest.mark.smoke
@pytest.mark.ui
async def test_programs_journey_smoke(page: Page) -> None:
    """
    Programs journey: navigate, filter, search.
    Validates the full flow works end-to-end with a real browser.
    """
    fake_user = _FakeUser()
    await run_programs_journey(page, fake_user)


@pytest.mark.smoke
@pytest.mark.ui
async def test_inventory_journey_smoke(page: Page) -> None:
    """
    Inventory journey: DX → Inventory → browse items.
    Validates model load, inventory navigation, and item links.
    """
    fake_user = _FakeUser()
    await run_inventory_journey(page, fake_user)


@pytest.mark.smoke
@pytest.mark.ui
async def test_dx_workflow_journey_smoke(page: Page) -> None:
    """
    DX journey: full multi-model workflow.
    Validates model switching, analysis radios, and filter comboboxes.
    """
    fake_user = _FakeUser()
    await run_dx_journey(page, fake_user)


@pytest.mark.smoke
@pytest.mark.ui
async def test_cytopedia_journey_smoke(page: Page) -> None:
    """
    CytoPedia journey: navigate, filter entities, search, open result.
    """
    fake_user = _FakeUser()
    await run_cytopedia_journey(page, fake_user)
