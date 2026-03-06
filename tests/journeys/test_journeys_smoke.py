import pytest

from src.ui.journeys.analyst import analyst_journey
from src.ui.journeys.viewer import viewer_journey
from src.ui.pages.login_page import LoginPage


@pytest.mark.smoke
async def test_journeys_smoke(page):
    lp = LoginPage(page)
    await lp.goto()
    await lp.login()
    await viewer_journey(page)
    await analyst_journey(page)
