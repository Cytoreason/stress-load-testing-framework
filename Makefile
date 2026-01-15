# Makefile for Load Testing Framework

.PHONY: help install setup test smoke load stress api pytest clean web

# Default target
help:
	@echo "Load Testing Framework - Available Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install     - Install dependencies"
	@echo "  make setup       - Complete setup (venv + install + config)"
	@echo ""
	@echo "Testing:"
	@echo "  make web         - Start Locust web UI"
	@echo "  make smoke       - Run quick smoke tests"
	@echo "  make load        - Run load tests"
	@echo "  make stress      - Run stress tests"
	@echo "  make api         - Run API tests"
	@echo "  make pytest      - Run pytest-based tests"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean       - Clean up reports and cache files"
	@echo "  make lint        - Run code linting"
	@echo ""

# Install dependencies
install:
	pip install -r requirements.txt

# Complete setup
setup:
	python -m venv venv
	@echo "Virtual environment created. Activate it with:"
	@echo "  source venv/bin/activate (Linux/Mac)"
	@echo "  venv\\Scripts\\activate (Windows)"
	@echo ""
	@echo "Then run: make install"

# Create .env file if it doesn't exist
.env:
	cp .env.example .env
	@echo ".env file created. Please edit it with your configuration."

# Start Locust web UI
web: .env
	locust -f locustfile.py --host $(shell grep BASE_URL .env | cut -d '=' -f2)

# Run smoke tests
smoke: .env
	mkdir -p reports
	locust -f locustfile.py \
		--host $(shell grep BASE_URL .env | cut -d '=' -f2) \
		--users 5 \
		--spawn-rate 1 \
		--run-time 30s \
		--headless \
		--html reports/smoke_test.html

# Run load tests
load: .env
	mkdir -p reports
	locust -f locustfile.py \
		--host $(shell grep BASE_URL .env | cut -d '=' -f2) \
		--users 10 \
		--spawn-rate 2 \
		--run-time 60s \
		--headless \
		--html reports/load_test.html

# Run stress tests
stress: .env
	mkdir -p reports
	locust -f locustfile.py \
		--host $(shell grep BASE_URL .env | cut -d '=' -f2) \
		--users 100 \
		--spawn-rate 10 \
		--run-time 300s \
		--headless \
		--html reports/stress_test.html

# Run API tests
api: .env
	mkdir -p reports
	locust -f locustfile.py \
		APIUser \
		--host $(shell grep BASE_URL .env | cut -d '=' -f2) \
		--users 15 \
		--spawn-rate 3 \
		--run-time 60s \
		--headless \
		--html reports/api_test.html

# Run pytest tests
pytest: .env
	pytest tests/ -v

# Run pytest with HTML report
pytest-html: .env
	mkdir -p reports
	pytest tests/ --html=reports/pytest_report.html --self-contained-html

# Run pytest smoke tests
pytest-smoke: .env
	pytest tests/ -m smoke -v

# Run pytest load tests
pytest-load: .env
	pytest tests/ -m load -v

# Run pytest stress tests
pytest-stress: .env
	pytest tests/ -m stress -v

# Clean up generated files
clean:
	rm -rf reports/*.html reports/*.csv reports/*.log
	rm -rf .pytest_cache
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "Cleanup completed"

# Run linting
lint:
	@which flake8 > /dev/null || pip install flake8
	flake8 locust_tests tests --max-line-length=100 --exclude=venv,__pycache__

# Format code
format:
	@which black > /dev/null || pip install black
	black locust_tests tests --line-length=100
