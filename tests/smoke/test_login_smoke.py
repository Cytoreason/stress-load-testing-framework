import pytest

from src.ui.pages.login_page import LoginPage


@pytest.mark.smoke
async def test_login_smoke(page):
    lp = LoginPage(page)
    await lp.goto()
    await lp.login()
