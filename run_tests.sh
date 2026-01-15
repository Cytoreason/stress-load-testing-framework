#!/bin/bash

# Load Testing Framework - Test Runner Script
# This script provides easy commands to run different types of load tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
HOST="${BASE_URL:-https://apps.private.cytoreason.com/platform/customers/pxx/}"
USERS="${USERS:-10}"
SPAWN_RATE="${SPAWN_RATE:-2}"
RUN_TIME="${RUN_TIME:-60s}"
REPORT_DIR="${REPORT_DIR:-./reports}"

# Create report directory
mkdir -p "$REPORT_DIR"

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
Load Testing Framework - Test Runner

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    web         Start Locust web UI
    smoke       Run quick smoke tests
    load        Run load tests
    stress      Run stress tests
    api         Run API tests
    pytest      Run pytest-based tests
    help        Show this help message

Options:
    --users N           Number of users (default: $USERS)
    --spawn-rate N      User spawn rate (default: $SPAWN_RATE)
    --run-time TIME     Test duration (default: $RUN_TIME)
    --host URL          Target host URL (default: $HOST)

Examples:
    $0 web
    $0 load --users 50 --run-time 300s
    $0 stress --users 100 --spawn-rate 10
    $0 pytest -m smoke

EOF
}

# Parse command line arguments
COMMAND="${1:-help}"
shift || true

while [[ $# -gt 0 ]]; do
    case $1 in
        --users)
            USERS="$2"
            shift 2
            ;;
        --spawn-rate)
            SPAWN_RATE="$2"
            shift 2
            ;;
        --run-time)
            RUN_TIME="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        *)
            PYTEST_ARGS="$PYTEST_ARGS $1"
            shift
            ;;
    esac
done

# Execute command
case $COMMAND in
    web)
        print_info "Starting Locust Web UI..."
        print_info "Open http://localhost:8089 in your browser"
        locust -f locustfile.py --host "$HOST"
        ;;

    smoke)
        print_info "Running smoke tests..."
        locust -f locustfile.py \
            --host "$HOST" \
            --users 5 \
            --spawn-rate 1 \
            --run-time 30s \
            --headless \
            --html "$REPORT_DIR/smoke_test_$(date +%Y%m%d_%H%M%S).html" \
            --csv "$REPORT_DIR/smoke_test_$(date +%Y%m%d_%H%M%S)"
        print_info "Smoke test completed. Report saved to $REPORT_DIR"
        ;;

    load)
        print_info "Running load tests..."
        print_info "Users: $USERS | Spawn Rate: $SPAWN_RATE | Duration: $RUN_TIME"
        locust -f locustfile.py \
            --host "$HOST" \
            --users "$USERS" \
            --spawn-rate "$SPAWN_RATE" \
            --run-time "$RUN_TIME" \
            --headless \
            --html "$REPORT_DIR/load_test_$(date +%Y%m%d_%H%M%S).html" \
            --csv "$REPORT_DIR/load_test_$(date +%Y%m%d_%H%M%S)"
        print_info "Load test completed. Report saved to $REPORT_DIR"
        ;;

    stress)
        print_info "Running stress tests with high load..."
        locust -f locustfile.py \
            --host "$HOST" \
            --users "${USERS:-100}" \
            --spawn-rate "${SPAWN_RATE:-10}" \
            --run-time "${RUN_TIME:-300s}" \
            --headless \
            --html "$REPORT_DIR/stress_test_$(date +%Y%m%d_%H%M%S).html" \
            --csv "$REPORT_DIR/stress_test_$(date +%Y%m%d_%H%M%S)"
        print_info "Stress test completed. Report saved to $REPORT_DIR"
        ;;

    api)
        print_info "Running API load tests..."
        locust -f locustfile.py \
            APIUser \
            --host "$HOST" \
            --users "$USERS" \
            --spawn-rate "$SPAWN_RATE" \
            --run-time "$RUN_TIME" \
            --headless \
            --html "$REPORT_DIR/api_test_$(date +%Y%m%d_%H%M%S).html" \
            --csv "$REPORT_DIR/api_test_$(date +%Y%m%d_%H%M%S)"
        print_info "API test completed. Report saved to $REPORT_DIR"
        ;;

    pytest)
        print_info "Running pytest-based tests..."
        pytest tests/ $PYTEST_ARGS
        print_info "Pytest tests completed"
        ;;

    help|--help|-h)
        show_usage
        ;;

    *)
        print_error "Unknown command: $COMMAND"
        show_usage
        exit 1
        ;;
esac
