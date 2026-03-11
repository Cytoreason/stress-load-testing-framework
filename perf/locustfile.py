"""
CytoReason UI Performance Framework – Locust entry point.

Architecture
------------
  - CytoreasonUiUser:  one Locust virtual user = one persistent browser context.
    - A single context is created at first task execution and reused for the
      entire user lifetime (realistic: one person, one browser tab session).
    - Auth0 login is performed ONCE per user lifecycle to minimise Auth0 load.
    - If the session expires or is corrupted, the context is transparently
      recreated and re-authenticated before retrying.

  - Task weighting reflects realistic usage distribution:
      Programs / Projects  : 35%  (most common landing + search workflow)
      Inventory            : 25%  (moderate; requires DX model load first)
      DX Workflow (full)   : 25%  (heavy; multi-model analysis journey)
      CytoPedia            : 15%  (moderate; knowledge base browsing)

  - Load shape:
      Selected via TEST_PROFILE env var.
      LOAD   → CytoreasonUiLoadShape   (perf/shape_load.py)
      STRESS → CytoreasonUiStressShape (perf/shape_stress.py)

  - Distributed:
      Launch master + N workers as described in the README.
      Each worker runs this locustfile.  The master aggregates all stats.

Metrics
-------
  - Each journey emits fine-grained named Locust events with the exact UI
    page or action name (prefix UI_).
  - MetricsCollector accumulates per-name samples.
  - PerformanceReporter writes JSON + CSV at end of run.
  - Worker health is checked at init time and every 60 s during the run.

Event names used (all follow the UI_<Verb>_<Screen/Action> convention):
  UI_Login_Auth0
  UI_Open_Programs_Page
  UI_Filter_Programs_My_Projects
  UI_Filter_Programs_All_Projects
  UI_Search_Programs_Query
  UI_Clear_Programs_Search
  UI_Open_DX_Differential_Expression_Page
  UI_Navigate_To_Inventory_Page
  UI_Expand_Inventory_Disease_Biology
  UI_Open_Inventory_Item_Target_Expression
  UI_Open_Inventory_Item_Target_Regulation
  UI_Open_Inventory_Item_Cell_Abundance
  UI_Open_Inventory_Item_Disease_Severity
  UI_Open_Inventory_Item_SOC_Treatment
  UI_Load_DX_Disease_Model_ASTH
  UI_Select_DX_White_Space_Analysis
  UI_Select_DX_Target_Signature_Analysis
  UI_Browse_DX_Filter_Bronchus
  UI_Browse_DX_Filter_Disease_Vs_Control
  UI_Browse_DX_Filter_Fluticasone
  UI_Browse_DX_Filter_Week1_500ug
  UI_Switch_DX_Disease_Model_COPD
  UI_Navigate_To_Inventory_Page_COPD
  UI_Open_Inventory_Item_Target_Expression_COPD
  UI_Switch_DX_Disease_Model_UC
  UI_Navigate_To_Inventory_Page_UC
  UI_Open_Inventory_Item_Target_Expression_UC
  UI_Open_CytoPedia_Page
  UI_Filter_CytoPedia_Entities_Category
  UI_Search_CytoPedia_Terms
  UI_Open_CytoPedia_Cell_Entities
"""
from __future__ import annotations

import logging
import time

import gevent
from locust import between, events, task
from locust_plugins.users import playwright as pw_plugin
from locust_plugins.users.playwright import PageWithRetry, PlaywrightUser, event
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from src.config import TestProfile, settings
from src.health.worker_health import assert_worker_healthy, check_worker_health
from src.telemetry.metrics import MetricsCollector
from src.telemetry.reporter import PerformanceReporter
from src.ui.journeys.cytopedia_journey import run_cytopedia_journey
from src.ui.journeys.dx_journey import run_dx_journey
from src.ui.journeys.inventory_journey import run_inventory_journey
from src.ui.journeys.programs_journey import run_programs_journey
from src.ui.pages.login_page import LoginPage
from src.ui.selectors import login_sel, ready_sel

# ---------------------------------------------------------------------------
# Shape selection – must be imported here so Locust auto-detects the class
# ---------------------------------------------------------------------------
if settings.test_profile == TestProfile.STRESS:
    from perf.shape_stress import CytoreasonUiStressShape as _ActiveShape  # noqa: F401
else:
    from perf.shape_load import CytoreasonUiLoadShape as _ActiveShape  # noqa: F401

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global metrics collector (all workers share the same env in single-node mode;
# in distributed mode each worker has its own collector and the master merges
# via Locust's built-in stats protocol).
# ---------------------------------------------------------------------------
_collector = MetricsCollector()
_reporter: PerformanceReporter | None = None


# ===========================================================================
# Locust lifecycle hooks
# ===========================================================================

@events.init.add_listener
def on_locust_init(environment, **_kwargs):
    """Run at initialisation – bind metrics + perform worker health pre-check."""
    global _reporter

    _collector.attach(environment)
    _reporter = PerformanceReporter(
        _collector,
        run_id=time.strftime("%Y%m%d_%H%M%S"),
        node_id=settings.node_id,
    )
    environment.events.quitting.add_listener(_reporter.on_quitting)

    # Pre-flight worker health check (warn only; don't abort the run)
    assert_worker_healthy(raise_on_critical=False)

    # Start background health monitor greenlet (fires every 60 s)
    def _health_loop():
        while True:
            gevent.sleep(60)
            check_worker_health()

    gevent.spawn(_health_loop)


@events.quitting.add_listener
def on_quitting(environment, **_kwargs):
    """Print the summary table to stdout at end of run."""
    if _reporter:
        _reporter.print_summary_table()


# ===========================================================================
# Session management helpers (used inside each task)
# ===========================================================================

async def _create_browser_context(user: PlaywrightUser) -> None:
    """
    Create a fresh browser context on the user, configure it, and bind the page.

    Called once at first task execution (lazy initialisation) and again if the
    session is determined to be corrupted.
    """
    # Close any existing context first
    ctx = getattr(user, "browser_context", None)
    if ctx is not None:
        try:
            await ctx.close()
        except Exception:
            pass

    new_ctx = await user.browser.new_context(
        ignore_https_errors=True,
        base_url=user.host,
        viewport=settings.viewport,
    )

    # Block media/fonts to reduce per-session bandwidth and CPU
    async def _route_handler(route, request):
        if request.resource_type in ("image", "media", "font"):
            await route.abort()
        else:
            await route.continue_()

    await new_ctx.route("**/*", _route_handler)

    page = await new_ctx.new_page()
    page.set_default_timeout(settings.default_timeout_ms)
    page.set_default_navigation_timeout(settings.navigation_timeout_ms)

    user.browser_context = new_ctx
    user.page = page
    user._session_ready = False
    user._logged_in = False
    user._error_screenshot_taken = False


async def _ensure_authenticated_session(user: PlaywrightUser) -> None:
    """
    Guarantee that the user has an active, authenticated browser session.

    - Creates the context on first call.
    - Performs Auth0 login once per context lifetime.
    - On session corruption (flagged by ``_session_ready = False``) recreates
      everything and re-authenticates.
    """
    if not getattr(user, "_session_ready", False):
        if not getattr(user, "browser_context", None):
            await _create_browser_context(user)

        async with event(user, "UI_Login_Auth0"):
            lp = LoginPage(user.page)
            await user.page.goto(settings.base_url, wait_until="networkidle")

            # Handle both direct Auth0 redirect and embedded login form
            if "auth0.com" in user.page.url:
                await lp.login()
            else:
                try:
                    await user.page.get_by_label(
                        login_sel.username_input_label
                    ).wait_for(state="visible", timeout=4_000)
                    await lp.login()
                except PlaywrightTimeoutError:
                    pass  # Already authenticated or no form present

            # Verify the app loaded correctly (2 attempts with reload)
            for attempt in range(2):
                try:
                    await user.page.wait_for_url(
                        f"**{settings.base_url}/**",
                        wait_until="networkidle",
                        timeout=settings.navigation_timeout_ms,
                    )
                    await user.page.get_by_role(
                        ready_sel.landing_unique_role,
                        name=ready_sel.landing_unique_name,
                    ).wait_for(state="visible", timeout=10_000)
                    break
                except PlaywrightTimeoutError:
                    if attempt == 0:
                        await user.page.reload(wait_until="networkidle")
                    else:
                        raise

        user._session_ready = True
        user._logged_in = True


# ===========================================================================
# Task decorator
# ===========================================================================

def ui_task(func):
    """
    Wraps an async task method so that it:
    1. Bridges async → sync for Locust (via @pw_plugin.sync).
    2. Ensures a healthy authenticated session before running.
    3. Takes a failure screenshot (once per session) on unhandled exceptions.
    4. Marks the session as needing reinitialisation on error so the next
       task call rebuilds the context.
    """

    @pw_plugin.sync
    async def _wrapper(user: PlaywrightUser):
        try:
            await _ensure_authenticated_session(user)
        except Exception as auth_err:
            # Authentication itself failed – report and invalidate session
            logger.warning(
                "[%s] Session init failed: %s", user.__class__.__name__, auth_err
            )
            user._session_ready = False
            raise

        try:
            await func(user, user.page)
        except PlaywrightTimeoutError as timeout_err:
            _handle_task_error(user, timeout_err)
            raise
        except Exception as err:
            _handle_task_error(user, err)
            raise

    _wrapper.__name__ = func.__name__
    return _wrapper


def _handle_task_error(user: PlaywrightUser, err: Exception) -> None:
    """Flag session for reinitialisation and optionally take a screenshot."""
    user._session_ready = False
    user._logged_in = False
    if not getattr(user, "_error_screenshot_taken", False) and getattr(user, "page", None):
        user._error_screenshot_taken = True
        import asyncio  # noqa: PLC0415
        try:
            ts = time.strftime("%Y%m%d_%H%M%S")
            path = settings.artifacts_dir / f"error_{ts}_{settings.node_id}.png"
            # Schedule screenshot asynchronously (best-effort)
            asyncio.ensure_future(
                user.page.screenshot(path=str(path), full_page=True)
            )
        except Exception:
            pass


# ===========================================================================
# User class
# ===========================================================================

class CytoreasonUiUser(PlaywrightUser):
    """
    Simulates a single CytoReason platform user with a persistent browser session.

    Task weights:
      Programs journey  : 7 (35%)
      Inventory journey : 5 (25%)
      DX journey        : 5 (25%)
      CytoPedia journey : 3 (15%)
    """

    host = settings.base_url
    wait_time = between(settings.think_time_min_s, settings.think_time_max_s)
    headless = settings.headless
    browser_type = settings.browser

    # ------------------------------------------------------------------ tasks

    @task(7)
    @ui_task
    async def UI_Browse_Programs_Page(self, page: PageWithRetry) -> None:
        """Programs / Projects page: open, filter, search."""
        await run_programs_journey(page, self)

    @task(5)
    @ui_task
    async def UI_Browse_Inventory_Page(self, page: PageWithRetry) -> None:
        """Disease Explorer → Inventory: navigate and browse items."""
        await run_inventory_journey(page, self)

    @task(5)
    @ui_task
    async def UI_Run_DX_Workflow(self, page: PageWithRetry) -> None:
        """Disease Explorer DX: multi-model analysis workflow."""
        await run_dx_journey(page, self)

    @task(3)
    @ui_task
    async def UI_Browse_CytoPedia(self, page: PageWithRetry) -> None:
        """CytoPedia: navigate, filter, search."""
        await run_cytopedia_journey(page, self)
