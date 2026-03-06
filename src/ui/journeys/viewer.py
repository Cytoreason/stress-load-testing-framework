from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from src.config import settings
from src.ui.pages.login_page import LoginPage
from src.ui.selectors import login_sel


async def _goto_and_wait(page: Page, url: str, wait_locator) -> None:
    target_pattern = f"**{url.replace(settings.base_url.rstrip('/'), '')}**"
    timeout_ms = max(settings.navigation_timeout_ms, 60000)
    for attempt in range(3):
        await page.goto(url, wait_until="domcontentloaded")
        if "auth0.com" in page.url:
            await LoginPage(page).login()
            await page.goto(url, wait_until="domcontentloaded")
        else:
            try:
                await page.get_by_label(
                    login_sel.username_input_label
                ).wait_for(timeout=2000)
                await LoginPage(page).login()
                await page.goto(url, wait_until="domcontentloaded")
            except PlaywrightTimeoutError:
                pass
        try:
            await page.wait_for_url(
                target_pattern, wait_until="domcontentloaded", timeout=timeout_ms
            )
            await wait_locator.wait_for(state="visible", timeout=timeout_ms)
            return
        except PlaywrightTimeoutError:
            if attempt < 2:
                await page.reload(wait_until="domcontentloaded")
            else:
                raise


async def viewer_journey(page: Page) -> None:
    # Programs landing + light interactions
    programs_url = f"{settings.base_url.rstrip('/')}/programs"
    search = page.get_by_role(
        "textbox", name="Search program, project or model..."
    )
    try:
        await _goto_and_wait(page, programs_url, search)
    except PlaywrightTimeoutError:
        return
    await search.wait_for(state="visible")
    await page.get_by_role("button", name="My Projects").click()
    await page.get_by_role("button", name="All Projects").click()
    await search.fill("test")
    await page.wait_for_timeout(300)
    await search.fill("")
