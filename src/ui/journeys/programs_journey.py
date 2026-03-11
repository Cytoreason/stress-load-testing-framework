"""
Programs / Projects journey.

Simulates a user visiting the Programs landing page, toggling project filters,
and performing a search.  Each distinct user action is timed and reported as
a named Locust event so metrics appear per-action in reports.

Locust event names emitted:
  - UI_Open_Programs_Page
  - UI_Filter_Programs_My_Projects
  - UI_Filter_Programs_All_Projects
  - UI_Search_Programs_Query
  - UI_Clear_Programs_Search
"""
from __future__ import annotations

from locust_plugins.users.playwright import event
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from src.ui.pages.programs_page import ProgramsPage


async def run_programs_journey(page: Page, user) -> None:
    """
    Execute the Programs page journey.

    Parameters
    ----------
    page : playwright.async_api.Page
        The Playwright page bound to the current Locust user session.
    user : PlaywrightUser
        Locust user instance; required for ``event()`` metric reporting.
    """
    pp = ProgramsPage(page)

    async with event(user, "UI_Open_Programs_Page"):
        await pp.open()

    async with event(user, "UI_Filter_Programs_My_Projects"):
        await pp.filter_my_projects()

    async with event(user, "UI_Filter_Programs_All_Projects"):
        await pp.filter_all_projects()

    async with event(user, "UI_Search_Programs_Query"):
        await pp.search("test")

    async with event(user, "UI_Clear_Programs_Search"):
        await pp.clear_search()
