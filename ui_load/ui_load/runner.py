"""
Load test runner - orchestrates virtual users and manages test lifecycle.
"""

from __future__ import annotations

import asyncio
import importlib
import logging
import signal
import sys
from pathlib import Path
from typing import Any

from playwright.async_api import Browser, Playwright, async_playwright

from ui_load.config import RunConfig
from ui_load.metrics import MetricsCollector
from ui_load.report import ReportWriter
from ui_load.user import ScenarioProtocol, VirtualUser

logger = logging.getLogger(__name__)


class LoadRunner:
    """
    Orchestrates load test execution.
    
    Manages:
    - Browser lifecycle
    - Virtual user creation and ramp-up
    - Graceful shutdown on Ctrl+C
    - Metrics collection and reporting
    """

    def __init__(self, config: RunConfig) -> None:
        self.config = config
        self.metrics = MetricsCollector(config.run_output_dir)
        self.report_writer = ReportWriter(config.run_output_dir)
        
        # Runtime state
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._users: list[VirtualUser] = []
        self._user_tasks: list[asyncio.Task[None]] = []
        self._stop_event = asyncio.Event()
        self._shutdown_requested = False
    
    async def setup(self) -> None:
        """Initialize Playwright and browser."""
        logger.info("Setting up Playwright browser")
        
        # Create output directories
        self.config.run_output_dir.mkdir(parents=True, exist_ok=True)
        self.config.videos_dir.mkdir(parents=True, exist_ok=True)
        if self.config.enable_tracing:
            self.config.traces_dir.mkdir(parents=True, exist_ok=True)
        
        # Launch Playwright
        self._playwright = await async_playwright().start()
        
        # Select browser type
        browser_type = getattr(self._playwright, self.config.browser.browser_type)
        
        # Launch browser
        self._browser = await browser_type.launch(
            headless=self.config.browser.headless,
            slow_mo=self.config.browser.slow_mo,
        )
        
        logger.info(
            f"Browser launched: {self.config.browser.browser_type} "
            f"(headless={self.config.browser.headless})"
        )
    
    async def teardown(self) -> None:
        """Clean up all resources."""
        logger.info("Tearing down runner")
        
        # Cancel all user tasks
        for task in self._user_tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete cancellation
        if self._user_tasks:
            await asyncio.gather(*self._user_tasks, return_exceptions=True)
        
        # Teardown all users (finalizes videos)
        teardown_tasks = [user.teardown() for user in self._users]
        if teardown_tasks:
            await asyncio.gather(*teardown_tasks, return_exceptions=True)
        
        # Close browser
        if self._browser:
            await self._browser.close()
            self._browser = None
        
        # Stop Playwright
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        
        logger.info("Teardown complete")
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        loop = asyncio.get_event_loop()
        
        def signal_handler(sig: signal.Signals) -> None:
            if self._shutdown_requested:
                logger.warning("Force shutdown requested, exiting immediately")
                sys.exit(1)
            
            logger.info(f"Received {sig.name}, initiating graceful shutdown...")
            self._shutdown_requested = True
            self._stop_event.set()
        
        # Register handlers
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, signal_handler, sig)
            except NotImplementedError:
                # Windows doesn't support add_signal_handler
                signal.signal(sig, lambda s, f: signal_handler(signal.Signals(s)))
    
    def load_scenario(self) -> ScenarioProtocol:
        """Load and instantiate the scenario module."""
        scenario_config = self.config.scenario
        
        # Determine module path
        if scenario_config.module_path:
            module_path = scenario_config.module_path
        else:
            # Default: scenarios.<name>
            module_path = f"scenarios.{scenario_config.name}"
        
        logger.info(f"Loading scenario: {module_path}")
        
        try:
            # Add scenarios directory to path if needed
            scenarios_dir = Path.cwd() / "scenarios"
            if scenarios_dir.exists() and str(scenarios_dir.parent) not in sys.path:
                sys.path.insert(0, str(scenarios_dir.parent))
            
            # Import the module
            module = importlib.import_module(module_path)
            
            # Find the scenario class
            # Convention: class name is CamelCase version of module name + "Scenario"
            # Or look for any class implementing run() method
            scenario_class = None
            
            for name in dir(module):
                obj = getattr(module, name)
                if (
                    isinstance(obj, type)
                    and name.endswith("Scenario")
                    and hasattr(obj, "run")
                ):
                    scenario_class = obj
                    break
            
            if scenario_class is None:
                raise ValueError(
                    f"No scenario class found in {module_path}. "
                    f"Class name must end with 'Scenario' and have a 'run' method."
                )
            
            # Instantiate with params
            return scenario_class(**scenario_config.params)
        
        except ImportError as e:
            raise ValueError(f"Could not import scenario module '{module_path}': {e}")
    
    async def run(self) -> dict[str, Any]:
        """
        Execute the load test.
        
        Returns:
            Summary results dictionary.
        """
        if not self._browser:
            raise RuntimeError("Runner not setup. Call setup() first.")
        
        scenario = self.load_scenario()
        self._setup_signal_handlers()
        
        logger.info(
            f"Starting load test: {self.config.load.users} users, "
            f"{self.config.load.ramp_up_seconds}s ramp-up, "
            f"{self.config.load.duration_seconds}s duration"
        )
        
        await self.metrics.start_run()
        
        try:
            # Ramp up users
            await self._ramp_up_users(scenario)
            
            # Wait for duration (or stop event)
            if not self._stop_event.is_set():
                logger.info(
                    f"Ramp-up complete. Running for {self.config.load.duration_seconds}s..."
                )
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=self.config.load.duration_seconds,
                    )
                except asyncio.TimeoutError:
                    # Normal completion
                    pass
            
            logger.info("Duration complete, stopping users...")
            self._stop_event.set()
        
        finally:
            # Signal all users to stop
            self._stop_event.set()
            
            # Wait for tasks with timeout
            if self._user_tasks:
                done, pending = await asyncio.wait(
                    self._user_tasks,
                    timeout=10,  # Give users 10s to finish current iteration
                )
                
                # Cancel any still running
                for task in pending:
                    task.cancel()
                
                if pending:
                    await asyncio.gather(*pending, return_exceptions=True)
            
            await self.metrics.end_run()
        
        # Generate report
        summary = self.metrics.compute_summary(self.config.model_dump())
        self.report_writer.write_summary(summary)
        
        logger.info(f"Results written to {self.config.run_output_dir}")
        
        return summary
    
    async def _ramp_up_users(self, scenario: ScenarioProtocol) -> None:
        """Gradually start virtual users over the ramp-up period."""
        interval = self.config.load.user_start_interval_seconds
        
        for user_id in range(1, self.config.load.users + 1):
            if self._stop_event.is_set():
                break
            
            # Create and setup user
            user = VirtualUser(
                user_id=user_id,
                browser=self._browser,  # type: ignore
                config=self.config,
                metrics=self.metrics,
                stop_event=self._stop_event,
            )
            
            await self.metrics.register_user(user_id)
            await user.setup()
            self._users.append(user)
            
            # Start user task
            task = asyncio.create_task(
                user.run_loop(scenario),
                name=f"user_{user_id}",
            )
            self._user_tasks.append(task)
            
            logger.info(f"Started user {user_id}/{self.config.load.users}")
            
            # Wait before starting next user (except for last one)
            if user_id < self.config.load.users and interval > 0:
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=interval,
                    )
                    if self._stop_event.is_set():
                        break
                except asyncio.TimeoutError:
                    pass


async def run_load_test(config: RunConfig) -> dict[str, Any]:
    """
    Convenience function to run a load test.
    
    Args:
        config: The run configuration.
    
    Returns:
        Summary results dictionary.
    """
    runner = LoadRunner(config)
    
    try:
        await runner.setup()
        return await runner.run()
    finally:
        await runner.teardown()
