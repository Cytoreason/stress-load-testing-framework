"""
Configuration loader for the load testing framework.

Provides centralized configuration management with type safety.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

__all__ = ["Config", "DiseaseConfig", "load_config", "get_config"]


@dataclass
class DiseaseConfig:
    """Configuration for a disease test scenario."""

    disease: str
    disease_name: str
    tissue: str
    context_ids: list[str] = field(default_factory=list)


@dataclass
class Config:
    """Main configuration container for load tests."""

    # Target settings
    base_url: str = "https://apps.private.cytoreason.com"
    api_base: str = "https://api.platform.private.cytoreason.com/v1.0"
    customer: str = "pyy"
    timeout: int = 30
    verify_ssl: bool = True

    # Authentication
    bearer_token: Optional[str] = None

    # Project configuration
    project_id: str = "main"
    project_version: str = "0.0.2"

    # Load test parameters
    users: int = 10
    spawn_rate: int = 1
    run_time: str = "60s"

    # Thresholds
    max_response_time_ms: int = 5000
    max_error_rate_percent: int = 5

    # Logging
    log_level: str = "INFO"

    # Disease configurations
    diseases: list[DiseaseConfig] = field(default_factory=list)

    @property
    def platform_base_path(self) -> str:
        """Get the platform base path for the customer."""
        return f"/platform/customers/{self.customer}"

    @property
    def api_platform_url(self) -> str:
        """Get the full API platform URL."""
        return f"{self.api_base}/customer/{self.customer}/e2/platform"

    @property
    def project_config(self) -> dict[str, str]:
        """Get project configuration dict for API payloads."""
        return {"id": self.project_id, "version": self.project_version}


# Module-level config cache
_config: Optional[Config] = None


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config file. If None, uses default location.

    Returns:
        Loaded Config instance

    Raises:
        FileNotFoundError: If config file doesn't exist
    """
    global _config

    if config_path is None:
        config_path = os.path.join(
            os.path.dirname(__file__), "..", "config", "config.yaml"
        )

    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        raw_config: dict[str, Any] = yaml.safe_load(f)

    # Extract values from nested YAML structure
    target = raw_config.get("target", {})
    auth = raw_config.get("auth", {})
    load_test = raw_config.get("load_test", {})
    thresholds = raw_config.get("thresholds", {})
    reporting = raw_config.get("reporting", {})

    # Build disease configs
    diseases = [
        DiseaseConfig(
            disease="celiac",
            disease_name="celiac",
            tissue="duodenum",
            context_ids=[
                "494f46e-e9a23cb-a7767bb-a7767bb",
                "494f46e-4c73c1b-f42422c-a7767bb",
                "494f46e-271369d-f42422c-a7767bb",
            ],
        ),
        DiseaseConfig(
            disease="ulcerative colitis",
            disease_name="ulcerative colitis",
            tissue="colon",
            context_ids=[
                "b9b43f9-e9a23cb-95997a7-95997a7",
                "b9b43f9-e9a23cb-688f3bf-688f3bf",
                "b9b43f9-25f2517-0d34eea-688f3bf",
            ],
        ),
        DiseaseConfig(
            disease="crohn disease",
            disease_name="crohn disease",
            tissue="colon",
            context_ids=[
                "b9b43f9-e9a23cb-95997a7-95997a7",
                "b9b43f9-e9a23cb-688f3bf-688f3bf",
            ],
        ),
        DiseaseConfig(
            disease="systemic sclerosis",
            disease_name="systemic sclerosis",
            tissue="skin",
            context_ids=[
                "494f46e-e9a23cb-a7767bb-a7767bb",
            ],
        ),
    ]

    _config = Config(
        base_url=target.get("base_url", Config.base_url).rstrip("/"),
        timeout=target.get("timeout", Config.timeout),
        verify_ssl=target.get("verify_ssl", Config.verify_ssl),
        bearer_token=auth.get("bearer_token") or None,
        users=load_test.get("users", Config.users),
        spawn_rate=load_test.get("spawn_rate", Config.spawn_rate),
        run_time=load_test.get("run_time", Config.run_time),
        max_response_time_ms=thresholds.get(
            "max_response_time_ms", Config.max_response_time_ms
        ),
        max_error_rate_percent=thresholds.get(
            "max_error_rate_percent", Config.max_error_rate_percent
        ),
        log_level=reporting.get("log_level", Config.log_level),
        diseases=diseases,
    )

    return _config


def get_config() -> Config:
    """
    Get the current configuration, loading it if necessary.

    Returns:
        Current Config instance
    """
    global _config

    if _config is None:
        try:
            _config = load_config()
        except FileNotFoundError:
            # Return default config if no file exists
            _config = Config()

    return _config
