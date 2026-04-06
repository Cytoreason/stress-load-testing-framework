"""
CytoPedia page object.

URL: {base_url}/cytopedia

LIVE VALIDATED (2026-03-11):
- Search textbox: matched by placeholder via accessible name ("Search terms by title or description")
- Entities button: get_by_role("button", name="Entities", exact=True).first  ✓
- Cell Entities: get_by_role("button", name="Cell Entities") ✓
  (rendered as a <button> in an expandable result list, NOT an <a> link)
- CytoPedia button list on Entities tab: Entities, Evidences, Methods, Concepts, QCM,
  followed by result items like "Cell Entities", "View All N Results"
"""
from __future__ import annotations

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from src.config import settings
from src.ui.pages.base_page import BasePage
from src.ui.selectors import cytopedia_sel


class CytopediaPage(BasePage):
    URL = f"{settings.base_url}{cytopedia_sel.cytopedia_path}"

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self._search = page.get_by_role(
            "textbox", name=cytopedia_sel.search_accessible_name
        )

    # ------------------------------------------------------------------ open
    async def open(self) -> None:
        await self.goto_url(self.URL, self._search)

    # ------------------------------------------------------------- categories
    async def filter_by_entities(self) -> None:
        btn = self.page.get_by_role(
            "button", name=cytopedia_sel.entities_button, exact=True
        ).first
        await self.safe_click(btn)
        # The filter click triggers an async API call that re-renders results.
        # Wait for network activity to settle so the next search fires against
        # the Entities-filtered index — not the unfiltered one.
        # networkidle has a 10 s cap; a fixed 5 s floor guards against SPAs
        # that never fully go idle (background polling, etc.).
        try:
            await self.page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:
            await self.page.wait_for_timeout(5_000)

    # ----------------------------------------------------------------- search
    async def search(self, query: str) -> None:
        # debounce_ms=2000 gives the filtered search API time to respond
        await self.fill_and_wait(self._search, query, debounce_ms=2_000)

    # ---------------------------------------------------------- result click
    async def open_cell_entities(self) -> None:
        """Poll for the Cell Entities result button with auth recovery.

        Polls in 8s chunks up to 120s.  On each miss: checks for an auth
        redirect and, if the page has left /cytopedia, re-navigates and
        re-runs filter + search before continuing to poll.
        """
        timeout_ms = max(settings.navigation_timeout_ms, 120_000)
        chunk_ms = 30_000   # 30 s covers typical search API response under load;
                            # 8 s was too short — results arrived after the chunk
                            # expired, causing false "not found" retries
        remaining_ms = timeout_ms

        while remaining_ms > 0:
            link = self.page.locator("button, a").filter(
                has_text=cytopedia_sel.cell_entities_link
            ).first
            try:
                await link.wait_for(state="visible", timeout=min(chunk_ms, remaining_ms))
                await link.click()
                return
            except (PlaywrightTimeoutError, PlaywrightError):
                remaining_ms -= chunk_ms
                await self._recover_auth_if_needed()
                if "/cytopedia" not in self.page.url:
                    # Auth redirect navigated us away — re-establish search state
                    nav_timeout = max(settings.navigation_timeout_ms, 60_000)
                    await self.page.goto(
                        self.URL, wait_until="domcontentloaded", timeout=nav_timeout
                    )
                    await self._search.wait_for(state="visible", timeout=30_000)
                    await self.filter_by_entities()
                    await self.search("cell")
                if remaining_ms <= 0:
                    raise PlaywrightTimeoutError(
                        f"Cell Entities not visible after {timeout_ms}ms"
                    )
