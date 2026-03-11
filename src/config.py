"""
Framework configuration.

All values read from environment variables (see .env.example).
A Settings instance is a frozen dataclass so it can be safely shared across
threads and async tasks without mutation risk.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class TestProfile(str, Enum):
    """Selects the load shape injected into Locust."""

    LOAD = "load"
    STRESS = "stress"


@dataclass(frozen=True)
class Settings:
    # ------------------------------------------------------------------ target
    base_url: str = field(
        default_factory=lambda: os.getenv("BASE_URL", "").strip().rstrip("/")
    )
    http_basic_user: str = field(
        default_factory=lambda: os.getenv("HTTP_BASIC_USER", "").strip()
    )
    http_basic_pass: str = field(
        default_factory=lambda: os.getenv("HTTP_BASIC_PASS", "").strip()
    )
    username: str = field(
        default_factory=lambda: os.getenv("USERNAME", "").strip()
    )
    password: str = field(
        default_factory=lambda: os.getenv("PASSWORD", "").strip()
    )

    # ----------------------------------------------------------------- browser
    headless: bool = field(
        default_factory=lambda: os.getenv("HEADLESS", "1") == "1"
    )
    browser: str = field(
        default_factory=lambda: os.getenv("BROWSER", "chromium").strip()
    )
    browser_width: int = field(
        default_factory=lambda: int(os.getenv("BROWSER_WIDTH", "1366"))
    )
    browser_height: int = field(
        default_factory=lambda: int(os.getenv("BROWSER_HEIGHT", "768"))
    )

    # ---------------------------------------------------------------- timeouts
    default_timeout_ms: int = field(
        default_factory=lambda: int(os.getenv("DEFAULT_TIMEOUT_MS", "30000"))
    )
    navigation_timeout_ms: int = field(
        default_factory=lambda: int(os.getenv("NAVIGATION_TIMEOUT_MS", "60000"))
    )

    # ------------------------------------------------------------- think time
    think_time_min_s: float = field(
        default_factory=lambda: float(os.getenv("THINK_TIME_MIN_S", "1.0"))
    )
    think_time_max_s: float = field(
        default_factory=lambda: float(os.getenv("THINK_TIME_MAX_S", "3.0"))
    )

    # -------------------------------------------------------------- concurrency
    peak_users: int = field(
        default_factory=lambda: int(os.getenv("PEAK_USERS", "100"))
    )

    # --------------------------------------------------------------- artifacts
    artifacts_dir: Path = field(
        default_factory=lambda: Path(os.getenv("ARTIFACTS_DIR", "artifacts"))
    )
    report_format: str = field(
        default_factory=lambda: os.getenv("REPORT_FORMAT", "both").strip()
    )

    # ----------------------------------------------------------------- profile
    test_profile: TestProfile = field(
        default_factory=lambda: TestProfile(
            os.getenv("TEST_PROFILE", "load").strip().lower()
        )
    )

    # -------------------------------------------------------------- distributed
    node_id: str = field(
        default_factory=lambda: os.getenv("NODE_ID", "worker-1").strip()
    )
    locust_master_host: str = field(
        default_factory=lambda: os.getenv("LOCUST_MASTER_HOST", "127.0.0.1").strip()
    )
    locust_master_port: int = field(
        default_factory=lambda: int(os.getenv("LOCUST_MASTER_PORT", "5557"))
    )

    def __post_init__(self) -> None:
        if not self.base_url:
            raise RuntimeError(
                "BASE_URL is required. Copy .env.example → .env and fill it in."
            )
        # Ensure artifact directory exists at import time so workers can write
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    # ----------------------------------------------------------------- helpers
    @property
    def viewport(self) -> dict[str, int]:
        return {"width": self.browser_width, "height": self.browser_height}

    @property
    def has_http_basic_auth(self) -> bool:
        return bool(self.http_basic_user and self.http_basic_pass)

    def base_url_with_auth(self) -> str:
        """Return URL with embedded HTTP Basic Auth credentials if configured."""
        if not self.has_http_basic_auth:
            return self.base_url
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(self.base_url)
        netloc = f"{self.http_basic_user}:{self.http_basic_pass}@{parsed.hostname}"
        if parsed.port:
            netloc += f":{parsed.port}"
        return urlunparse(parsed._replace(netloc=netloc))


settings = Settings()
