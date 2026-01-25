"""
Test data loading utilities.

Provides CSV and JSON data reading capabilities for load testing,
supporting credential files, test data sets, and configuration files.
"""

import csv
import json
import logging
import random
from pathlib import Path
from typing import Any, Iterator, Optional

from common.config import get_config

logger = logging.getLogger(__name__)


class DataLoader:
    """
    Test data loader for CSV and JSON files.
    
    Supports loading credentials, test data sets, and iterating
    through data for parameterized load tests.
    """
    
    def __init__(self, data_path: Optional[str] = None):
        """
        Initialize the data loader.
        
        Args:
            data_path: Base path for data files. Defaults to config setting.
        """
        config = get_config()
        self.data_path = Path(data_path or config.test_data_path)
        self._cache: dict[str, Any] = {}
    
    def load_csv(self, filename: str, cache: bool = True) -> list[dict]:
        """
        Load data from a CSV file.
        
        Args:
            filename: Name of the CSV file (relative to data_path)
            cache: Whether to cache the loaded data
            
        Returns:
            List of dictionaries, one per row
        """
        cache_key = f"csv:{filename}"
        if cache and cache_key in self._cache:
            return self._cache[cache_key]
        
        file_path = self.data_path / filename
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                data = list(reader)
            
            logger.info(f"Loaded {len(data)} rows from {filename}")
            
            if cache:
                self._cache[cache_key] = data
            return data
        except FileNotFoundError:
            logger.warning(f"CSV file not found: {file_path}")
            return []
        except Exception as e:
            logger.error(f"Error loading CSV {filename}: {e}")
            return []
    
    def load_json(self, filename: str, cache: bool = True) -> Any:
        """
        Load data from a JSON file.
        
        Args:
            filename: Name of the JSON file (relative to data_path)
            cache: Whether to cache the loaded data
            
        Returns:
            Parsed JSON data (dict or list)
        """
        cache_key = f"json:{filename}"
        if cache and cache_key in self._cache:
            return self._cache[cache_key]
        
        file_path = self.data_path / filename
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            logger.info(f"Loaded JSON from {filename}")
            
            if cache:
                self._cache[cache_key] = data
            return data
        except FileNotFoundError:
            logger.warning(f"JSON file not found: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {filename}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading JSON {filename}: {e}")
            return {}
    
    def load_credentials(self, filename: str = "credentials.csv") -> list[tuple[str, str]]:
        """
        Load user credentials from a CSV file.
        
        Expected CSV format:
            username,password
            user1,pass1
            user2,pass2
        
        Args:
            filename: Name of the credentials CSV file
            
        Returns:
            List of (username, password) tuples
        """
        data = self.load_csv(filename)
        credentials = []
        for row in data:
            username = row.get("username", "").strip()
            password = row.get("password", "").strip()
            if username and password:
                credentials.append((username, password))
        
        logger.info(f"Loaded {len(credentials)} credentials from {filename}")
        return credentials
    
    def get_random_item(self, filename: str, file_type: str = "json") -> Any:
        """
        Get a random item from a data file.
        
        Args:
            filename: Name of the data file
            file_type: Type of file ('json' or 'csv')
            
        Returns:
            Random item from the file, or None if file is empty
        """
        if file_type == "csv":
            data = self.load_csv(filename)
        else:
            data = self.load_json(filename)
        
        if isinstance(data, list) and data:
            return random.choice(data)
        return None
    
    def iterate_data(self, filename: str, file_type: str = "json") -> Iterator[Any]:
        """
        Create an iterator over data file contents.
        
        Useful for parameterized tests that need to cycle through test data.
        
        Args:
            filename: Name of the data file
            file_type: Type of file ('json' or 'csv')
            
        Yields:
            Items from the data file
        """
        if file_type == "csv":
            data = self.load_csv(filename)
        else:
            data = self.load_json(filename)
        
        if isinstance(data, list):
            for item in data:
                yield item
    
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        logger.debug("Data cache cleared")
