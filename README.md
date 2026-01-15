# Load Testing Framework with Locust.io

A comprehensive load testing framework built with Locust.io, pytest, and Python for testing the Cytoreason platform at `https://apps.private.cytoreason.com/platform/customers/pxx/`.

## Features

- **Locust.io Integration**: Powerful load testing with easy-to-write Python tests
- **Pytest Integration**: Run load tests with pytest for better reporting and CI/CD integration
- **Configurable**: YAML-based configuration with environment variable overrides
- **Multiple Test Scenarios**: Basic load, stress, spike, and endurance test scenarios
- **Authentication Support**: Token, Basic Auth, API Key authentication methods
- **Comprehensive Utilities**: Helper functions for test data generation, logging, and more
- **HTML Reports**: Generate detailed HTML reports of test results
- **Flexible User Simulation**: Multiple user behavior patterns and sequential workflows

## Project Structure

```
stress-load-testing-framework/
├── locust_tests/
│   ├── config/
│   │   ├── config.yaml          # Main configuration file
│   │   └── settings.py          # Configuration loader
│   ├── locustfiles/
│   │   ├── base_user.py         # Base user class with common functionality
│   │   └── example_test.py      # Example test scenarios
│   └── utils/
│       ├── auth.py              # Authentication utilities
│       ├── helpers.py           # Helper functions
│       └── logger.py            # Logging utilities
├── tests/
│   ├── conftest.py              # Pytest fixtures and configuration
│   └── test_load_scenarios.py  # Pytest-based load tests
├── reports/                     # Test reports directory
├── locustfile.py               # Main Locust entry point
├── requirements.txt            # Python dependencies
├── pytest.ini                  # Pytest configuration
├── .env.example               # Example environment variables
└── README.md                  # This file
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd stress-load-testing-framework
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Configuration

### YAML Configuration

Edit `locust_tests/config/config.yaml` to customize:
- Target URL and connection settings
- Load test parameters (users, spawn rate, duration)
- Test scenarios
- Authentication settings
- Performance thresholds

### Environment Variables

Create a `.env` file with the following variables:

```env
BASE_URL=https://apps.private.cytoreason.com/platform/customers/pxx/
USERS=10
SPAWN_RATE=1
RUN_TIME=60s
AUTH_TOKEN=your_token_here
LOG_LEVEL=INFO
REPORT_DIR=./reports
```

## Usage

### Running with Locust Web UI

Start the Locust web interface:

```bash
locust -f locustfile.py --host https://apps.private.cytoreason.com/platform/customers/pxx/
```

Then open your browser to `http://localhost:8089` to configure and start the test.

### Running with Locust CLI (Headless)

Run a load test without the web UI:

```bash
# Basic load test
locust -f locustfile.py \
    --host https://apps.private.cytoreason.com/platform/customers/pxx/ \
    --users 10 \
    --spawn-rate 2 \
    --run-time 60s \
    --headless \
    --html reports/report.html

# Stress test with more users
locust -f locustfile.py \
    --host https://apps.private.cytoreason.com/platform/customers/pxx/ \
    --users 100 \
    --spawn-rate 10 \
    --run-time 300s \
    --headless \
    --html reports/stress_test.html

# Run specific user class
locust -f locustfile.py \
    --host https://apps.private.cytoreason.com/platform/customers/pxx/ \
    CustomerPlatformUser \
    --users 20 \
    --spawn-rate 4 \
    --run-time 120s \
    --headless
```

### Running with Pytest

Run load tests with pytest:

```bash
# Run all tests
pytest tests/

# Run with HTML report
pytest tests/ --html=reports/pytest_report.html

# Run specific test markers
pytest tests/ -m smoke         # Quick smoke tests
pytest tests/ -m load          # Load tests
pytest tests/ -m stress        # Stress tests
pytest tests/ -m integration   # Integration tests

# Run specific test
pytest tests/test_load_scenarios.py::test_basic_load_scenario

# Run with verbose output
pytest tests/ -v -s
```

## Test Scenarios

### CustomerPlatformUser
Simulates typical user browsing behavior:
- View homepage (weight: 3)
- View dashboard (weight: 2)
- View reports (weight: 1)
- View analytics (weight: 1)

### SequentialUser
Follows a sequential user journey:
1. Login page
2. Dashboard
3. View data
4. Reports
5. Logout

### APIUser
Simulates API interactions:
- Get customer data (weight: 3)
- Get platform status (weight: 2)
- Post analytics events (weight: 1)

## Creating Custom Tests

### Example: Custom User Class

```python
from locust import task, between
from locust_tests.locustfiles.base_user import BaseLoadTestUser

class MyCustomUser(BaseLoadTestUser):
    wait_time = between(1, 3)

    @task(3)
    def my_custom_task(self):
        """Custom task implementation"""
        response = self.get("/my-endpoint")
        self.validate_response(response, expected_status=200)

    @task(1)
    def another_task(self):
        """Another custom task"""
        data = {"key": "value"}
        self.post("/api/endpoint", json_data=data)
```

### Example: Sequential Tasks

```python
from locust import SequentialTaskSet, task
from locust_tests.locustfiles.base_user import BaseLoadTestUser

class MySequentialTasks(SequentialTaskSet):
    @task
    def first_step(self):
        self.client.get("/step1")

    @task
    def second_step(self):
        self.client.post("/step2", json={"data": "value"})

class MyUser(BaseLoadTestUser):
    tasks = [MySequentialTasks]
```

## Monitoring and Reports

### Locust Reports

Locust generates HTML reports with:
- Request statistics (RPS, response times, failures)
- Response time distribution
- Number of users over time
- Failures and errors

### Pytest Reports

Pytest can generate HTML reports with:
- Test results and outcomes
- Test duration
- Logs and error messages
- Custom test metadata

### Performance Metrics

The framework tracks:
- Total requests
- Failed requests
- Success rate
- Average response time
- Maximum response time
- Requests per second
- Percentiles (50th, 95th, 99th)

## Performance Thresholds

Configure thresholds in `config.yaml`:

```yaml
thresholds:
  max_response_time_ms: 5000
  max_error_rate_percent: 5
  min_requests_per_second: 10
```

## Best Practices

1. **Start Small**: Begin with a small number of users and gradually increase
2. **Monitor Resources**: Watch server CPU, memory, and network usage
3. **Use Realistic Data**: Generate realistic test data with the helper functions
4. **Set Think Time**: Use appropriate wait times between requests
5. **Handle Errors**: Use `catch_response` context manager for custom error handling
6. **Test in Stages**: Run smoke tests before full load tests
7. **Document Results**: Keep records of test configurations and results

## Troubleshooting

### Connection Issues

If you encounter connection errors:
- Verify the target URL is accessible
- Check authentication credentials
- Disable SSL verification if using self-signed certificates (set `verify_ssl: false` in config)

### High Failure Rates

If tests show high failure rates:
- Reduce the number of users or spawn rate
- Check if the target server is healthy
- Review server logs for errors
- Adjust request timeouts

### Import Errors

If you encounter import errors:
- Ensure virtual environment is activated
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check Python path includes project root

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Load Tests

on:
  schedule:
    - cron: '0 2 * * *'  # Run daily at 2 AM
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -m smoke
      - run: pytest tests/ -m load --html=reports/report.html
      - uses: actions/upload-artifact@v2
        with:
          name: load-test-reports
          path: reports/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions:
- Open an issue on GitHub
- Contact the development team
- Check the Locust documentation: https://docs.locust.io/
