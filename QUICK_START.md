# Quick Start Guide

Get started with load testing in 5 minutes!

## 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

## 2. Configure Your Test

Create a `.env` file:

```bash
cp .env.example .env
```

Edit `.env` and set your target URL:
```env
BASE_URL=https://apps.private.cytoreason.com/platform/customers/pxx/
```

## 3. Run Your First Test

### Option A: Use the Web UI (Recommended for first-time users)

```bash
locust -f locustfile.py
```

Then open http://localhost:8089 in your browser.

### Option B: Run Headless (CLI)

```bash
# Quick smoke test (5 users, 30 seconds)
./run_tests.sh smoke

# Basic load test (10 users, 60 seconds)
./run_tests.sh load

# Custom load test
./run_tests.sh load --users 20 --run-time 120s
```

### Option C: Use Pytest

```bash
# Run smoke tests
pytest tests/ -m smoke

# Run all load tests
pytest tests/ -m load

# Run with HTML report
pytest tests/ --html=reports/report.html
```

## 4. View Results

Results are saved in the `reports/` directory:
- HTML reports with graphs and statistics
- CSV files with detailed metrics
- Pytest HTML reports with test outcomes

## Common Commands

```bash
# Run stress test with 100 users
./run_tests.sh stress --users 100 --run-time 300s

# Run API-specific tests
./run_tests.sh api --users 15

# Run pytest integration tests
pytest tests/ -m integration -v
```

## Next Steps

1. **Customize Tests**: Edit `locust_tests/locustfiles/example_test.py` to match your application
2. **Adjust Configuration**: Modify `locust_tests/config/config.yaml` for your needs
3. **Add Authentication**: Set auth tokens in `.env` file
4. **Create Custom Scenarios**: Follow examples in README.md

## Need Help?

- Check the full README.md for detailed documentation
- Review example tests in `locust_tests/locustfiles/`
- Visit https://docs.locust.io/ for Locust documentation
