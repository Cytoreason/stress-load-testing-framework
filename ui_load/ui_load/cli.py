"""
Command-line interface for UI load testing framework.

Usage:
    ui_load run --scenario example_login_browse --base-url https://example.com --users 10
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

import click

from ui_load.config import (
    BrowserConfig,
    LoadProfile,
    RunConfig,
    ScenarioConfig,
    SecurityConfig,
    VideoConfig,
)
from ui_load.report import print_summary
from ui_load.runner import run_load_test
from ui_load.utils import setup_logging, validate_scenario_name

logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="1.0.0", prog_name="ui_load")
def main() -> None:
    """
    UI Load Testing Framework - Playwright-based browser load testing.
    
    ⚠️  AUTHORIZED TESTING ONLY ⚠️
    
    Only use against systems you own or have explicit authorization to test.
    """
    pass


@main.command()
@click.option(
    "--scenario", "-s",
    required=True,
    help="Scenario name (module in scenarios/ directory).",
)
@click.option(
    "--base-url", "-u",
    required=True,
    help="Target base URL (e.g., https://staging.example.com).",
)
@click.option(
    "--users", "-n",
    default=5,
    type=click.IntRange(1, 1000),
    help="Number of concurrent virtual users (default: 5).",
)
@click.option(
    "--ramp-up", "-r",
    default=30,
    type=click.IntRange(0, 3600),
    help="Ramp-up time in seconds (default: 30).",
)
@click.option(
    "--duration", "-d",
    default=60,
    type=click.IntRange(1, 86400),
    help="Test duration in seconds after ramp-up (default: 60).",
)
@click.option(
    "--think-time-ms",
    default=1000,
    type=click.IntRange(0, 60000),
    help="Think time between iterations in ms (default: 1000).",
)
@click.option(
    "--timeout-ms",
    default=30000,
    type=click.IntRange(1000, 300000),
    help="Default page timeout in ms (default: 30000).",
)
@click.option(
    "--headless/--headed",
    default=True,
    help="Run browser in headless mode (default: headless).",
)
@click.option(
    "--browser",
    type=click.Choice(["chromium", "firefox", "webkit"]),
    default="chromium",
    help="Browser engine to use (default: chromium).",
)
@click.option(
    "--video-size",
    default="1280x720",
    help="Video recording size WxH (default: 1280x720).",
)
@click.option(
    "--no-video",
    is_flag=True,
    help="Disable video recording.",
)
@click.option(
    "--trace",
    is_flag=True,
    help="Enable Playwright tracing (generates .zip trace files).",
)
@click.option(
    "--output-dir", "-o",
    type=click.Path(path_type=Path),
    default=Path("./output"),
    help="Output directory for results (default: ./output).",
)
@click.option(
    "--allow-domain",
    multiple=True,
    help="Additional allowed domain patterns (regex).",
)
@click.option(
    "--no-domain-check",
    is_flag=True,
    help="Disable strict domain allowlist check (DANGEROUS).",
)
@click.option(
    "--max-users",
    default=100,
    type=click.IntRange(1, 10000),
    help="Maximum users safety limit (default: 100).",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    default="INFO",
    help="Log level (default: INFO).",
)
@click.option(
    "--scenario-param",
    multiple=True,
    help="Scenario parameters as key=value pairs.",
)
def run(
    scenario: str,
    base_url: str,
    users: int,
    ramp_up: int,
    duration: int,
    think_time_ms: int,
    timeout_ms: int,
    headless: bool,
    browser: str,
    video_size: str,
    no_video: bool,
    trace: bool,
    output_dir: Path,
    allow_domain: tuple[str, ...],
    no_domain_check: bool,
    max_users: int,
    log_level: str,
    scenario_param: tuple[str, ...],
) -> None:
    """
    Run a load test scenario.
    
    Example:
    
        ui_load run --scenario example_login_browse \\
                    --base-url https://staging.example.com \\
                    --users 20 --ramp-up 30 --duration 120
    """
    # Validate scenario name
    if not validate_scenario_name(scenario):
        raise click.BadParameter(
            "Scenario name must start with a letter and contain only "
            "alphanumeric characters, underscores, and hyphens."
        )
    
    # Parse video size
    try:
        width, height = map(int, video_size.split("x"))
    except ValueError:
        raise click.BadParameter(
            f"Invalid video-size format: {video_size}. Expected WxH (e.g., 1280x720)."
        )
    
    # Parse scenario parameters
    params: dict[str, Any] = {}
    for param in scenario_param:
        if "=" not in param:
            raise click.BadParameter(
                f"Invalid scenario-param format: {param}. Expected key=value."
            )
        key, value = param.split("=", 1)
        # Try to parse as JSON for complex values
        try:
            import json
            params[key] = json.loads(value)
        except json.JSONDecodeError:
            params[key] = value
    
    # Build security config
    allowed_domains = list(SecurityConfig().allowed_domains)
    for domain in allow_domain:
        allowed_domains.append(domain)
    
    security_config = SecurityConfig(
        allowed_domains=allowed_domains,
        strict_domain_check=not no_domain_check,
        max_users=max_users,
    )
    
    # Build configuration
    try:
        config = RunConfig(
            base_url=base_url,
            scenario=ScenarioConfig(
                name=scenario,
                params=params,
            ),
            load=LoadProfile(
                users=users,
                ramp_up_seconds=ramp_up,
                duration_seconds=duration,
                think_time_ms=think_time_ms,
            ),
            browser=BrowserConfig(
                headless=headless,
                browser_type=browser,
                timeout_ms=timeout_ms,
            ),
            video=VideoConfig(
                enabled=not no_video,
                width=width,
                height=height,
            ),
            security=security_config,
            output_dir=output_dir,
            enable_tracing=trace,
        )
    except ValueError as e:
        raise click.ClickException(str(e))
    
    # Setup logging
    setup_logging(
        level=log_level,
        log_file=config.run_output_dir / "run.log",
    )
    
    # Print startup banner
    click.echo()
    click.secho("=" * 60, fg="cyan")
    click.secho("  UI Load Testing Framework", fg="cyan", bold=True)
    click.secho("  ⚠️  AUTHORIZED TESTING ONLY", fg="yellow")
    click.secho("=" * 60, fg="cyan")
    click.echo()
    click.echo(f"  Run ID:      {config.run_id}")
    click.echo(f"  Scenario:    {scenario}")
    click.echo(f"  Base URL:    {base_url}")
    click.echo(f"  Users:       {users}")
    click.echo(f"  Ramp-up:     {ramp_up}s")
    click.echo(f"  Duration:    {duration}s")
    click.echo(f"  Output:      {config.run_output_dir}")
    click.echo()
    
    # Run the test
    try:
        summary = asyncio.run(_run_async(config))
        
        # Print summary
        print_summary(summary)
        
        # Check for failures
        overall = summary.get("overall", {})
        if overall.get("failed_iterations", 0) > 0:
            click.secho(
                f"⚠️  Test completed with {overall['failed_iterations']} failed iterations",
                fg="yellow",
            )
            sys.exit(1)
        else:
            click.secho("✓ Test completed successfully", fg="green")
    
    except KeyboardInterrupt:
        click.echo("\n")
        click.secho("Test interrupted by user", fg="yellow")
        sys.exit(130)
    
    except Exception as e:
        logger.exception("Test failed with exception")
        click.secho(f"✗ Test failed: {e}", fg="red")
        sys.exit(1)


async def _run_async(config: RunConfig) -> dict[str, Any]:
    """Async wrapper for running load test."""
    return await run_load_test(config)


@main.command()
def list_scenarios() -> None:
    """List available scenarios in the scenarios/ directory."""
    scenarios_dir = Path.cwd() / "scenarios"
    
    if not scenarios_dir.exists():
        click.echo("No scenarios/ directory found.")
        return
    
    click.echo("\nAvailable scenarios:\n")
    
    for path in sorted(scenarios_dir.glob("*.py")):
        if path.name.startswith("_"):
            continue
        
        name = path.stem
        
        # Try to read docstring
        try:
            with open(path) as f:
                content = f.read()
                
            # Simple docstring extraction
            import ast
            tree = ast.parse(content)
            docstring = ast.get_docstring(tree) or "No description"
            first_line = docstring.split("\n")[0]
        except Exception:
            first_line = "No description"
        
        click.echo(f"  {name}")
        click.echo(f"      {first_line}")
        click.echo()


@main.command()
@click.argument("run_id")
@click.option(
    "--output-dir", "-o",
    type=click.Path(path_type=Path, exists=True),
    default=Path("./output"),
    help="Output directory containing runs.",
)
def show(run_id: str, output_dir: Path) -> None:
    """Show results from a previous run."""
    import json
    
    run_dir = output_dir / "runs" / run_id
    summary_path = run_dir / "summary.json"
    
    if not summary_path.exists():
        raise click.ClickException(f"Run not found: {run_id}")
    
    with open(summary_path) as f:
        summary = json.load(f)
    
    print_summary(summary)


if __name__ == "__main__":
    main()
