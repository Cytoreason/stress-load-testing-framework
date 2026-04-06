"""
Disease Explorer / DX page object.

URL: {base_url}/disease-explorer/differential-expression

LIVE VALIDATED (2026-03-11):
- Model picker is a <button role="combobox"> with NO aria-label.
  Must use locator("button").filter(has_text="Disease Model").first
- Analysis type toggles are <button role="radio">: Target Gene, Target Signature,
  Meta Analysis, Per Dataset.  "White Space" does NOT exist on this page.
- Filter comboboxes are Radix UI select triggers with no aria-label;
  identified by has_text of their current displayed value.
- Model picker dropdown items (no space between abbr and name):
  ASTHAsthma, CECeliac Disease, COPDChronic Obstructive Pulmonary Disease,
  CDCrohn's Disease, SSCSystemic Sclerosis, UCUlcerative Colitis
- Inventory side-nav: role=link name="Inventory"
"""
from __future__ import annotations

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from src.config import settings
from src.ui.pages.base_page import BasePage
from src.ui.selectors import dx_sel, inventory_sel


# Model abbreviation → inventory URL slug.
# Validated on staging 2026-03-11: slugs are the lowercase model abbreviations,
# except ASTH → "asthma" (full name).  All others match abbreviation lowercase.
_ABBR_TO_INVENTORY_SLUG: dict[str, str] = {
    "ASTH": "asthma",
    "CE": "ce",
    "COPD": "copd",
    "CD": "cd",
    "SSC": "ssc",
    "UC": "uc",
}


def _inventory_url(slug: str) -> str:
    return f"{settings.base_url.rstrip('/')}/disease-explorer/model-inventory/{slug}"


class DxPage(BasePage):
    URL = f"{settings.base_url}{dx_sel.de_path}"

    # Pre-built inventory URLs — no DOM needed, zero latency.
    ASTH_INVENTORY_URL = _inventory_url("asthma")
    COPD_INVENTORY_URL = _inventory_url("copd")
    UC_INVENTORY_URL = _inventory_url("uc")

    def __init__(self, page: Page) -> None:
        super().__init__(page)
        # Model picker button (page-ready signal).
        # No aria-label → must use has_text filter.
        self._model_picker = page.locator("button").filter(
            has_text=dx_sel.model_picker_has_text
        ).first

    # ------------------------------------------------------------------ open
    # DX page ready timeout: model picker needs API data to load.
    # Under load the server can be slow; 90 s covers p99 from observed runs.
    _READY_TIMEOUT_MS = 90_000

    async def open(self) -> None:
        """Navigate to the DX page.

        Uses URL-only readiness — the model picker is API-loaded and must not
        block navigation.  Call ``wait_for_model_loaded()`` explicitly when
        the picker is needed before interacting with it.
        """
        await self.goto_url(self.URL)

    async def wait_for_model_loaded(self) -> None:
        """Wait for the model picker button to appear (confirms page rendered)."""
        await self._model_picker.wait_for(state="visible", timeout=self._READY_TIMEOUT_MS)

    # ---------------------------------------------------------- model picker
    async def open_model_picker(self) -> None:
        """Click the model picker to reveal the model selection dropdown.

        Dismisses any stray open dropdowns first (filter comboboxes left open
        by a prior action) so their [role='option'] items don't pollute the
        global portal DOM when we search for model picker options.
        Skips the click when the model picker is already open.
        """
        # Close any open Radix portals before opening the model picker
        await self.page.keyboard.press("Escape")
        await self.page.wait_for_timeout(200)
        state = await self._model_picker.get_attribute("data-state")
        if state == "open":
            return
        await self.safe_click(self._model_picker)

    async def select_model_from_dropdown(self, has_text: str) -> None:
        """
        Click the model in the open dropdown whose text contains *has_text*.

        Radix Select renders option items as ``[role='option']`` in a portal
        overlay.  We wait for the option directly; if not found within 12 s
        the picker may have closed so we re-click and retry once.

        Parameters
        ----------
        has_text : str
            Substring of the model name, e.g. "Chronic Obstructive Pulmonary Disease"
            for COPD, or "Ulcerative Colitis" for UC.
        """
        # Broad selector: original live-validated approach covers all Radix/Shadcn
        # renderings regardless of element type (div, li, a, button, [role='option']).
        # Uses state="attached" (not "visible") because Radix CSS enter-animations
        # briefly keep opacity:0, which causes wait_for("visible") to time out.
        # force=True on click bypasses residual actionability checks mid-animation.
        item = self.page.locator(
            "a, button, li, [role='option'], [data-radix-collection-item]"
        ).filter(has_text=has_text).first

        async def _find_and_click_option(attached_timeout_ms: int) -> None:
            await item.wait_for(state="attached", timeout=attached_timeout_ms)
            await item.scroll_into_view_if_needed()
            await item.click(force=True)

        try:
            await _find_and_click_option(30_000)
        except PlaywrightTimeoutError:
            # Picker may have closed — dismiss any overlay, reopen, retry
            await self.page.keyboard.press("Escape")
            await self.page.wait_for_timeout(500)
            await self.safe_click(self._model_picker)
            await _find_and_click_option(60_000)

        # Wait for the model picker to reflect the new model (SPA re-rendered).
        await self._recover_auth_if_needed()
        await self._model_picker.wait_for(state="visible", timeout=self._READY_TIMEOUT_MS)

    # ------------------------------------------------------- analysis toggles
    async def select_target_gene_analysis(self) -> None:
        """Select the Target Gene analysis type (role=radio button)."""
        await self._model_picker.wait_for(
            state="visible", timeout=settings.navigation_timeout_ms
        )
        await self.safe_click(
            self.page.get_by_role("radio", name=dx_sel.radio_target_gene),
            timeout_ms=settings.navigation_timeout_ms,
        )

    async def select_target_signature_analysis(self) -> None:
        """Select the Target Signature analysis type (role=radio button)."""
        await self._model_picker.wait_for(
            state="visible", timeout=settings.navigation_timeout_ms
        )
        await self.safe_click(
            self.page.get_by_role("radio", name=dx_sel.radio_target_signature),
            timeout_ms=settings.navigation_timeout_ms,
        )

    # ------------------------------------------------------- filter comboboxes
    async def open_and_dismiss_combobox(self, has_text: str) -> None:
        """
        Open a filter combobox (identified by *has_text* of its current value)
        then dismiss with Escape to simulate a user browsing options.

        Best-effort: skips silently if the combobox isn't visible (e.g. the
        filter panel shows different defaults after an analysis-type switch).
        """
        combo = self.page.locator("button[role='combobox']").filter(
            has_text=has_text
        ).first
        try:
            await combo.wait_for(state="visible", timeout=8_000)
            await combo.click()
            await self.page.keyboard.press("Escape")
        except PlaywrightTimeoutError:
            pass  # Filter may be absent for this analysis type; skip

    # --------------------------------------------------------- inventory nav
    async def navigate_to_inventory(self, url: str | None = None) -> None:
        """Navigate directly to the Inventory page.

        Pass one of the pre-built class-level URL constants (``ASTH_INVENTORY_URL``,
        ``COPD_INVENTORY_URL``, ``UC_INVENTORY_URL``) to avoid any DOM dependency.
        If *url* is omitted, falls back to reading the model picker text to derive
        the slug — but callers should always pass the URL explicitly.

        Never waits for the sidebar Inventory link.  That element is a separate
        lazy-loaded API call that can stall for 120 s+ under load.
        """
        timeout_ms = max(settings.navigation_timeout_ms, 60_000)

        if url is None:
            # Derive from model picker text (fallback; may fail mid-auth-redirect)
            try:
                picker_text = await self._model_picker.inner_text(timeout=10_000)
                abbr = picker_text.strip().splitlines()[0].strip()
                slug = _ABBR_TO_INVENTORY_SLUG.get(abbr)
                if slug:
                    url = _inventory_url(slug)
            except (PlaywrightTimeoutError, PlaywrightError):
                pass

        last_err: Exception | None = None
        for attempt in range(3):
            try:
                if url:
                    await self.page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                else:
                    raise PlaywrightTimeoutError("Could not determine inventory URL")

                await self._recover_auth_if_needed()
                if "disease-explorer/model-inventory" not in self.page.url:
                    await self.page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)

                await self.page.wait_for_url(
                    "**/disease-explorer/model-inventory/**",
                    wait_until="domcontentloaded",
                    timeout=timeout_ms,
                )
                return
            except (PlaywrightTimeoutError, PlaywrightError) as exc:
                last_err = exc
                if attempt < 2:
                    await self.page.wait_for_timeout(1_000)

        raise last_err  # type: ignore[misc]
