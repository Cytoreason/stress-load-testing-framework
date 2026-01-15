"""
Helper utilities for load testing
"""
import random
import string
import time
from typing import Any, Dict, List
from faker import Faker

fake = Faker()


def generate_random_string(length: int = 10) -> str:
    """
    Generate a random string

    Args:
        length: Length of the string

    Returns:
        Random string
    """
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_random_email() -> str:
    """
    Generate a random email address

    Returns:
        Random email address
    """
    return fake.email()


def generate_random_name() -> str:
    """
    Generate a random full name

    Returns:
        Random name
    """
    return fake.name()


def generate_random_data(data_type: str = "string", **kwargs) -> Any:
    """
    Generate random data based on type

    Args:
        data_type: Type of data to generate
        **kwargs: Additional parameters for data generation

    Returns:
        Generated random data
    """
    generators = {
        "string": lambda: generate_random_string(kwargs.get("length", 10)),
        "email": lambda: generate_random_email(),
        "name": lambda: generate_random_name(),
        "phone": lambda: fake.phone_number(),
        "address": lambda: fake.address(),
        "company": lambda: fake.company(),
        "url": lambda: fake.url(),
        "integer": lambda: random.randint(kwargs.get("min", 0), kwargs.get("max", 100)),
        "float": lambda: random.uniform(kwargs.get("min", 0.0), kwargs.get("max", 100.0)),
        "boolean": lambda: random.choice([True, False]),
        "date": lambda: fake.date(),
        "datetime": lambda: fake.date_time().isoformat(),
    }

    generator = generators.get(data_type, generators["string"])
    return generator()


def wait_random(min_wait: float = 1, max_wait: float = 5):
    """
    Wait for a random time between min_wait and max_wait

    Args:
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds
    """
    time.sleep(random.uniform(min_wait, max_wait))


def parse_response_time(response_time_ms: float) -> str:
    """
    Parse response time to human-readable format

    Args:
        response_time_ms: Response time in milliseconds

    Returns:
        Formatted response time string
    """
    if response_time_ms < 1000:
        return f"{response_time_ms:.2f}ms"
    else:
        return f"{response_time_ms / 1000:.2f}s"


def calculate_percentile(values: List[float], percentile: float) -> float:
    """
    Calculate percentile value from a list of values

    Args:
        values: List of values
        percentile: Percentile to calculate (0-100)

    Returns:
        Percentile value
    """
    if not values:
        return 0

    sorted_values = sorted(values)
    index = int((percentile / 100) * len(sorted_values))
    index = min(index, len(sorted_values) - 1)
    return sorted_values[index]


def create_test_data(template: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create test data from a template with random values

    Args:
        template: Template dictionary with data types

    Returns:
        Dictionary with generated test data
    """
    result = {}

    for key, value in template.items():
        if isinstance(value, dict):
            result[key] = create_test_data(value)
        elif isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
            # Parse template variable like "{{type:params}}"
            data_type = value.strip("{}").split(":")[0]
            result[key] = generate_random_data(data_type)
        else:
            result[key] = value

    return result
