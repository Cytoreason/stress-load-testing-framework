import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    base_url: str = os.getenv("BASE_URL", "").strip()
    username: str = os.getenv("USERNAME", "").strip()
    password: str = os.getenv("PASSWORD", "").strip()

    headless: bool = os.getenv("HEADLESS", "1") == "1"
    browser: str = os.getenv("BROWSER", "chromium").strip()

    default_timeout_ms: int = int(os.getenv("DEFAULT_TIMEOUT_MS", "30000"))
    navigation_timeout_ms: int = int(os.getenv("NAVIGATION_TIMEOUT_MS", "45000"))

    think_time_min_s: float = float(os.getenv("THINK_TIME_MIN_S", "1"))
    think_time_max_s: float = float(os.getenv("THINK_TIME_MAX_S", "3"))


settings = Settings()
if not settings.base_url:
    raise RuntimeError("BASE_URL is required (see .env.example)")
