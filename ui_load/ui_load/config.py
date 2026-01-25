"""
Configuration models for UI load testing framework.

Provides type-safe configuration with validation using Pydantic.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator, model_validator


class VideoConfig(BaseModel):
    """Video recording configuration."""

    enabled: bool = True
    width: int = Field(default=1280, ge=320, le=3840)
    height: int = Field(default=720, ge=240, le=2160)

    @property
    def size(self) -> dict[str, int]:
        """Return video size as dict for Playwright."""
        return {"width": self.width, "height": self.height}


class BrowserConfig(BaseModel):
    """Browser configuration."""

    headless: bool = True
    slow_mo: int = Field(default=0, ge=0, description="Slow down operations by ms")
    timeout_ms: int = Field(default=30000, ge=1000, le=300000)
    viewport_width: int = Field(default=1920, ge=320)
    viewport_height: int = Field(default=1080, ge=240)
    
    # Browser type: chromium, firefox, webkit
    browser_type: str = Field(default="chromium")
    
    @field_validator("browser_type")
    @classmethod
    def validate_browser_type(cls, v: str) -> str:
        allowed = {"chromium", "firefox", "webkit"}
        if v.lower() not in allowed:
            raise ValueError(f"browser_type must be one of {allowed}")
        return v.lower()


class LoadProfile(BaseModel):
    """Load profile configuration."""

    # Number of concurrent virtual users (default conservative)
    users: Annotated[int, Field(ge=1, le=1000)] = 5
    
    # Ramp-up period in seconds
    ramp_up_seconds: Annotated[int, Field(ge=0, le=3600)] = 30
    
    # Total test duration in seconds (after ramp-up completes)
    duration_seconds: Annotated[int, Field(ge=1, le=86400)] = 60
    
    # Think time between iterations (milliseconds)
    think_time_ms: Annotated[int, Field(ge=0, le=60000)] = 1000
    
    # Think time jitter (+/- percentage)
    think_time_jitter_pct: Annotated[float, Field(ge=0, le=100)] = 20.0
    
    @property
    def user_start_interval_seconds(self) -> float:
        """Calculate interval between starting users during ramp-up."""
        if self.users <= 1 or self.ramp_up_seconds == 0:
            return 0.0
        return self.ramp_up_seconds / self.users


class SecurityConfig(BaseModel):
    """Security configuration to prevent accidental misuse."""

    # Allowlist of domain patterns (regex)
    allowed_domains: list[str] = Field(
        default_factory=lambda: [
            r"^localhost(:\d+)?$",
            r"^127\.0\.0\.1(:\d+)?$",
            r"^.*\.local(:\d+)?$",
            r"^.*\.test(:\d+)?$",
            r"^.*\.example\.com(:\d+)?$",
            # CytoReason platform domains
            r"^apps\.private\.cytoreason\.com$",
            r"^.*\.cytoreason\.com$",
        ]
    )
    
    # If True, require explicit domain allowlist match
    strict_domain_check: bool = True
    
    # Maximum users allowed (safety limit)
    max_users: int = Field(default=100, ge=1)
    
    def is_domain_allowed(self, url: str) -> bool:
        """Check if URL's domain is in the allowlist."""
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        for pattern in self.allowed_domains:
            if re.match(pattern, domain, re.IGNORECASE):
                return True
        return False


class ScenarioConfig(BaseModel):
    """Configuration for a specific scenario."""

    name: str = Field(min_length=1, max_length=100)
    module_path: str | None = None  # e.g., "scenarios.example_login_browse"
    
    # Scenario-specific parameters passed to run()
    params: dict[str, Any] = Field(default_factory=dict)


class RunConfig(BaseModel):
    """Complete configuration for a load test run."""

    # Run identification
    run_id: str = Field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    
    # Target configuration
    base_url: str
    scenario: ScenarioConfig
    
    # Load profile
    load: LoadProfile = Field(default_factory=LoadProfile)
    
    # Browser settings
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    
    # Video settings
    video: VideoConfig = Field(default_factory=VideoConfig)
    
    # Security settings
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    
    # Output settings
    output_dir: Path = Field(default=Path("./output"))
    
    # Enable Playwright tracing (generates .zip trace files)
    enable_tracing: bool = False
    
    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Validate base URL format."""
        parsed = urlparse(v)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("base_url must be a valid URL with scheme and host")
        if parsed.scheme not in ("http", "https"):
            raise ValueError("base_url must use http or https scheme")
        return v.rstrip("/")
    
    @model_validator(mode="after")
    def validate_security(self) -> "RunConfig":
        """Validate security constraints."""
        # Check domain allowlist
        if self.security.strict_domain_check:
            if not self.security.is_domain_allowed(self.base_url):
                raise ValueError(
                    f"Domain not in allowlist: {self.base_url}. "
                    f"Add domain pattern to allowed_domains or disable strict_domain_check."
                )
        
        # Enforce max users
        if self.load.users > self.security.max_users:
            raise ValueError(
                f"User count {self.load.users} exceeds max_users limit {self.security.max_users}. "
                f"Increase max_users in security config if authorized."
            )
        
        return self
    
    @property
    def run_output_dir(self) -> Path:
        """Get the output directory for this specific run."""
        return self.output_dir / "runs" / self.run_id
    
    @property
    def videos_dir(self) -> Path:
        """Get the videos directory for this run."""
        return self.run_output_dir / "videos"
    
    @property
    def traces_dir(self) -> Path:
        """Get the traces directory for this run."""
        return self.run_output_dir / "traces"
    
    def get_user_video_dir(self, user_id: int) -> Path:
        """Get video directory for a specific user."""
        return self.videos_dir / f"user_{user_id}"
    
    def get_user_trace_path(self, user_id: int, iteration: int) -> Path:
        """Get trace file path for a specific user iteration."""
        return self.traces_dir / f"user_{user_id}_iter_{iteration}.zip"
