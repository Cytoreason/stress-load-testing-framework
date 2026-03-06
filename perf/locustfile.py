import random

from locust import between, task
from locust_plugins.users import playwright as pw_plugin
from locust_plugins.users.playwright import PageWithRetry, PlaywrightUser, event
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from src.config import settings
from src.ui.journeys.analyst import analyst_journey
from src.ui.journeys.admin import admin_journey
from src.ui.journeys.viewer import viewer_journey
from src.ui.pages.login_page import LoginPage
from src.ui.selectors import ready_sel

# Import the shape so Locust auto-detects it (must be in locustfile import graph)
from perf.shape import CytoreasonUiShape  # noqa: F401


def pw_safe(func):
    @pw_plugin.sync
    async def pwwrap(user: PlaywrightUser):
        if user.browser_context:
            await user.browser_context.close()
        user.browser_context = await user.browser.new_context(
            ignore_https_errors=True,
            base_url=user.host,
            viewport={"width": 1365, "height": 768},
        )
        user.page = await user.browser_context.new_page()
        user.page.set_default_timeout(settings.default_timeout_ms)
        user._logged_in = False

        async def _route_handler(route, request):
            if request.resource_type in ("image", "media", "font"):
                await route.abort()
            else:
                await route.continue_()

        await user.page.route("**/*", _route_handler)

        name = user.__class__.__name__ + "." + func.__name__
        try:
            task_start_time = pw_plugin.time.time()
            start_perf_counter = pw_plugin.time.perf_counter()
            await func(user, user.page)
            if user.log_tasks:
                user.environment.events.request.fire(
                    request_type="TASK",
                    name=name,
                    start_time=task_start_time,
                    response_time=(pw_plugin.time.perf_counter() - start_perf_counter)
                    * 1000,
                    response_length=0,
                    context={**user.context()},
                    exception=None,
                )
        except pw_plugin.RescheduleTask:
            pass
        except Exception as e:
            try:
                e = pw_plugin.CatchResponseError(
                    pw_plugin.re.sub(
                        "=======*", "", e.message + user.page.url
                    ).replace("\n", "")
                )
            except Exception:
                pass
            if not user.error_screenshot_made and user.page:
                user.error_screenshot_made = True
                await user.page.screenshot(
                    path="screenshot_" + pw_plugin.time.strftime("%Y%m%d_%H%M%S") + ".png",
                    full_page=True,
                )
            if user.log_tasks:
                user.environment.events.request.fire(
                    request_type="TASK",
                    name=name,
                    start_time=task_start_time,
                    response_time=(pw_plugin.time.perf_counter() - start_perf_counter)
                    * 1000,
                    response_length=0,
                    context={**user.context()},
                    exception=e,
                    url=user.page.url if user.page else None,
                )
            else:
                user.environment.events.user_error.fire(
                    user_instance=user, exception=e, tb=e.__traceback__
                )
        finally:
            try:
                if user.page and not user.page.is_closed():
                    await user.page.wait_for_timeout(200)
            except Exception:
                pass
            try:
                if user.page and not user.page.is_closed():
                    await user.page.close()
            except Exception:
                pass
            try:
                if user.browser_context:
                    await user.browser_context.close()
            except Exception:
                pass

    return pwwrap


class CytoreasonUiUser(PlaywrightUser):
    """
    A single Locust "user" that drives a real browser session.

    IMPORTANT:
    - Each user logs in once, then repeats actions.
    - Tasks are weighted to simulate different usage.
    """

    host = settings.base_url
    wait_time = between(settings.think_time_min_s, settings.think_time_max_s)
    multiplier = 1
    headless = settings.headless
    browser_type = settings.browser
    _logged_in = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logged_in = False

    async def _ensure_login(self, page: PageWithRetry) -> None:
        if getattr(self, "_logged_in", False):
            return
        async with event(self, "01_login"):
            lp = LoginPage(page)
            await page.goto(settings.base_url, wait_until="domcontentloaded")
            # If we're redirected to Auth0 or see login form, perform login
            if "auth0.com" in page.url:
                await lp.login()
            else:
                try:
                    await page.get_by_role(
                        ready_sel.landing_unique_role,
                        name=ready_sel.landing_unique_name,
                    ).wait_for(state="visible", timeout=3000)
                except PlaywrightTimeoutError:
                    await lp.goto()
                    await lp.login()

            for attempt in range(2):
                await page.goto(settings.base_url, wait_until="domcontentloaded")
                if "auth0.com" in page.url:
                    await lp.login()
                try:
                    await page.wait_for_url(
                        f"**{settings.base_url.strip('/')}/**",
                        wait_until="domcontentloaded",
                        timeout=settings.navigation_timeout_ms,
                    )
                except PlaywrightTimeoutError:
                    if attempt == 0:
                        await lp.goto()
                        await lp.login()
                        continue
                try:
                    await page.get_by_role(
                        ready_sel.landing_unique_role,
                        name=ready_sel.landing_unique_name,
                    ).wait_for(
                        state="visible",
                        timeout=5000,
                    )
                except PlaywrightTimeoutError:
                    # Continue even if ready selector is slow; journeys will re-sync.
                    pass
                self._logged_in = True
                return

            raise PlaywrightTimeoutError("Login failed after retries")
        self._logged_in = True

    @task(6)
    @pw_safe
    async def dashboard_light(self, page: PageWithRetry):
        await self._ensure_login(page)
        async with event(self, "02_dashboard_light"):
            await viewer_journey(page)

    @task(3)
    @pw_safe
    async def navigation_medium(self, page: PageWithRetry):
        await self._ensure_login(page)
        async with event(self, "03_navigation_medium"):
            await analyst_journey(page)

    @task(1)
    @pw_safe
    async def heavy_flow(self, page: PageWithRetry):
        await self._ensure_login(page)
        async with event(self, "04_heavy_flow"):
            await admin_journey(page)

    @task(1)
    @pw_safe
    async def random_idle_think_time(self, page: PageWithRetry):
        await self._ensure_login(page)
        async with event(self, "think_time"):
            await page.wait_for_timeout(random.randint(250, 1250))
