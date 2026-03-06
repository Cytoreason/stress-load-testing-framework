import re

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


async def admin_journey(page: Page) -> None:
    # Disease Models navigation + light exploration
    disease_url = (
        f"{settings.base_url.rstrip('/')}/disease-explorer/differential-expression"
    )
    model_combo = page.get_by_role("combobox", name="ASTH Disease Model Asthma")
    try:
        await _goto_and_wait(page, disease_url, model_combo)
        await model_combo.wait_for(
            state="visible", timeout=settings.navigation_timeout_ms
        )
    except PlaywrightTimeoutError:
        return
    await page.get_by_role("link", name="Inventory").click()
    await page.get_by_role("button", name="Disease Biology").click()
    await page.get_by_role("link", name="2 . Target Regulation in Disease").click()
    await page.get_by_role(
        "link", name="3 . Differential Cell Abundance in Disease"
    ).click()
    await page.get_by_role(
        "link", name="7 . Association with disease severity"
    ).click()
    await page.get_by_role(
        "link",
        name="8 . Standard of care (SOC) treatment effect spaces",
    ).click()
    await page.get_by_role("radio", name="White Space").click()
    await page.get_by_role("radio", name="Target Signature").click()
    for combo_name in [
        "bronchus",
        "disease vs control",
        "Fluticasone",
        "Week 1, 500 μg",
    ]:
        await page.get_by_role("combobox", name=combo_name).click()
        await page.keyboard.press("Escape")
    await page.wait_for_timeout(400)

    # Additional disease models
    for model_link, model_combo in [
        (re.compile(r"^COPD\b"), re.compile(r"COPD Disease Model")),
        (re.compile(r"^UC\b"), re.compile(r"UC Disease Model")),
    ]:
        await page.get_by_role("button", name="Disease Models").click()
        await page.get_by_role("link", name=model_link).click()
        await page.get_by_role("combobox", name=model_combo).wait_for(
            state="visible"
        )
        await page.get_by_role("link", name="Inventory").click()
        await page.get_by_role(
            "link", name="1 . Target Expression in Disease"
        ).click()
        await page.wait_for_timeout(300)
