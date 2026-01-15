"""
Configuration settings loader for the load testing framework
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Configuration management class"""

    def __init__(self, config_file: str = None):
        """
        Initialize configuration

        Args:
            config_file: Path to YAML configuration file
        """
        self.config_file = config_file or self._get_default_config_path()
        self._config_data = self._load_config()
        self._override_with_env()

    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        config_dir = Path(__file__).parent
        return str(config_dir / "config.yaml")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Warning: Config file {self.config_file} not found. Using defaults.")
            return {}
        except yaml.YAMLError as e:
            print(f"Error parsing config file: {e}")
            return {}

    def _override_with_env(self):
        """Override config values with environment variables"""
        # Target URL
        if os.getenv('BASE_URL'):
            self._config_data.setdefault('target', {})['base_url'] = os.getenv('BASE_URL')

        # Load test parameters
        if os.getenv('USERS'):
            self._config_data.setdefault('load_test', {})['users'] = int(os.getenv('USERS'))

        if os.getenv('SPAWN_RATE'):
            self._config_data.setdefault('load_test', {})['spawn_rate'] = int(os.getenv('SPAWN_RATE'))

        if os.getenv('RUN_TIME'):
            self._config_data.setdefault('load_test', {})['run_time'] = os.getenv('RUN_TIME')

        # Authentication
        if os.getenv('API_KEY'):
            self._config_data.setdefault('auth', {})['api_key'] = os.getenv('API_KEY')

        if os.getenv('USERNAME'):
            self._config_data.setdefault('auth', {})['username'] = os.getenv('USERNAME')

        if os.getenv('PASSWORD'):
            self._config_data.setdefault('auth', {})['password'] = os.getenv('PASSWORD')

        if os.getenv('AUTH_TOKEN'):
            self._config_data.setdefault('auth', {})['token'] = os.getenv('AUTH_TOKEN')

        # Reporting
        if os.getenv('REPORT_DIR'):
            self._config_data.setdefault('reporting', {})['output_dir'] = os.getenv('REPORT_DIR')

        if os.getenv('LOG_LEVEL'):
            self._config_data.setdefault('reporting', {})['log_level'] = os.getenv('LOG_LEVEL')

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key (supports nested keys with dot notation)

        Args:
            key: Configuration key (e.g., 'target.base_url')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config_data

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

            if value is None:
                return default

        return value

    @property
    def base_url(self) -> str:
        """Get base URL for the target application"""
        return self.get('target.base_url', 'https://apps.private.cytoreason.com/platform/customers/pxx/')

    @property
    def users(self) -> int:
        """Get number of users for load test"""
        return self.get('load_test.users', 10)

    @property
    def spawn_rate(self) -> int:
        """Get spawn rate for load test"""
        return self.get('load_test.spawn_rate', 1)

    @property
    def run_time(self) -> str:
        """Get run time for load test"""
        return self.get('load_test.run_time', '60s')

    @property
    def timeout(self) -> int:
        """Get request timeout"""
        return self.get('target.timeout', 30)

    @property
    def auth_token(self) -> str:
        """Get authentication token"""
        return self.get('auth.token', '')

    @property
    def report_dir(self) -> str:
        """Get report output directory"""
        return self.get('reporting.output_dir', './reports')

    def get_scenario(self, scenario_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific test scenario

        Args:
            scenario_name: Name of the scenario

        Returns:
            Scenario configuration dictionary
        """
        return self.get(f'scenarios.{scenario_name}', {})


# Global configuration instance
config = Config()
