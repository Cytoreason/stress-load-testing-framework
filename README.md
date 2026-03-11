# CytoReason UI Performance Testing Framework

Production-grade **UI-only** load and stress testing framework for the CytoReason staging platform.

**Stack**: Python · Pytest · Playwright · Locust

Target: `https://apps.private.cytoreason.com/platform/customers/pyy/`

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Locust Orchestration Layer                │
│  CytoreasonUiUser  ─  task weighting  ─  LoadShape          │
│  Master / Worker distributed execution                       │
└────────────────────┬────────────────────────────────────────┘
                     │  spawns
┌────────────────────▼────────────────────────────────────────┐
│                  Playwright Browser Layer                    │
│  Persistent BrowserContext per user  ─  route intercept     │
│  LoginPage  ─  ProgramsPage  ─  DxPage  ─  InventoryPage   │
│  CytopediaPage                                              │
└────────────────────┬────────────────────────────────────────┘
                     │  executed by
┌────────────────────▼────────────────────────────────────────┐
│                    Workflow / Journey Layer                  │
│  run_programs_journey  ─  run_inventory_journey             │
│  run_dx_journey        ─  run_cytopedia_journey             │
│  Each action wrapped: event(user, "UI_<Page>_<Action>")     │
└────────────────────┬────────────────────────────────────────┘
                     │  feeds
┌────────────────────▼────────────────────────────────────────┐
│                  Metrics / Reporting Layer                   │
│  MetricsCollector  ─  per-name percentile calculation       │
│  PerformanceReporter  ─  JSON + CSV export                  │
└─────────────────────────────────────────────────────────────┘
                     │  validated by
┌────────────────────▼────────────────────────────────────────┐
│               Validation / Support Layer (Pytest)           │
│  conftest.py authenticated_context  ─  smoke tests          │
│  selector validation  ─  journey end-to-end smoke tests     │
└─────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
stress-load-testing-framework/
├── .env.example                   # All env var documentation
├── pyproject.toml                 # Pytest config + markers
├── requirements.txt
│
├── src/
│   ├── config.py                  # Settings + profile selection
│   ├── health/
│   │   └── worker_health.py       # Worker CPU/RAM/FD monitor
│   ├── telemetry/
│   │   ├── metrics.py             # Per-name sample accumulator + percentiles
│   │   ├── reporter.py            # JSON + CSV export
│   │   └── timings.py             # Sync timing context manager (Pytest use)
│   └── ui/
│       ├── selectors.py           # All validated DOM selectors
│       ├── pages/
│       │   ├── base_page.py       # Shared navigation + interaction helpers
│       │   ├── login_page.py      # Auth0 login page object
│       │   ├── programs_page.py   # /programs page object
│       │   ├── inventory_page.py  # Inventory sub-page object
│       │   ├── dx_page.py         # /disease-explorer/differential-expression
│       │   └── cytopedia_page.py  # /cytopedia page object
│       └── journeys/
│           ├── journey_catalog.py       # Registry of all journeys
│           ├── programs_journey.py      # Programs + Projects workflow
│           ├── inventory_journey.py     # DX → Inventory workflow
│           ├── dx_journey.py            # Multi-model DX workflow
│           └── cytopedia_journey.py     # CytoPedia browse workflow
│
├── perf/
│   ├── locustfile.py              # Main Locust entry point
│   ├── shape_load.py              # Load test step-ramp shape
│   └── shape_stress.py            # Stress ramp-to-break shape
│
├── tests/
│   ├── conftest.py                # Fixtures: authenticated context + page
│   ├── smoke/
│   │   ├── test_login_smoke.py           # Auth0 login smoke
│   │   └── test_selector_validation.py   # DOM selector validation
│   └── journeys/
│       └── test_journeys_smoke.py        # End-to-end journey smoke tests
│
└── docker/
    ├── Dockerfile.worker          # Worker image (Locust + Chromium)
    └── docker-compose.yml         # 1 master + N workers topology
```

---

## Setup

```bash
# 1. Clone and enter the repo
git clone <repo-url>
cd stress-load-testing-framework

# 2. Create virtualenv
python3.11 -m venv .venv && source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright Chromium
playwright install chromium --with-deps

# 5. Configure environment
cp .env.example .env
# Edit .env: set BASE_URL, USERNAME, PASSWORD
```

---

## Running Tests

### Pre-flight Smoke Checks (mandatory before any load run)

```bash
# Run all smoke tests (login + selectors + journeys)
pytest -m smoke -v

# Selector-only validation
pytest -m selector -v

# Individual journey smoke
pytest tests/journeys/test_journeys_smoke.py::test_dx_workflow_journey_smoke -v
```

All smoke tests must pass before proceeding to load or stress runs.

---

## Running Load Tests

### Single-node Load Test

```bash
# Step-ramp load test (default TEST_PROFILE=load, 100 peak users)
TEST_PROFILE=load \
  locust \
    -f perf/locustfile.py \
    --users 100 \
    --headless \
    --html artifacts/load_report.html \
    --csv artifacts/load \
    -H $BASE_URL

# Custom peak: 50 users
PEAK_USERS=50 TEST_PROFILE=load \
  locust -f perf/locustfile.py --users 50 --headless
```

### Single-node Stress Test

```bash
# Ramp-to-break stress test (TEST_PROFILE=stress)
TEST_PROFILE=stress \
  locust \
    -f perf/locustfile.py \
    --users 100 \
    --headless \
    --html artifacts/stress_report.html \
    --csv artifacts/stress \
    -H $BASE_URL
```

---

## Distributed Execution (Recommended for 100 Users)

> 100 concurrent headless Chromium sessions require multiple machines.
> Guideline: **15–20 users per worker**. Use **5–7 workers** for 100 users.

### Manual Distribution

**On the master node:**
```bash
locust \
  --master \
  --master-bind-host=0.0.0.0 \
  --master-bind-port=5557 \
  -f perf/locustfile.py \
  --web-host=0.0.0.0 \
  --web-port=8089 \
  --expect-workers=6 \
  --loglevel=INFO
```

**On each worker node** (copy repo + .env):
```bash
LOCUST_MASTER_HOST=<master-ip> \
NODE_ID=worker-$(hostname) \
  locust \
    --worker \
    --master-host=<master-ip> \
    --master-port=5557 \
    -f perf/locustfile.py \
    --loglevel=INFO
```

Then open `http://<master-ip>:8089` to configure peak users and start the run.

### Docker Compose Distribution

```bash
# Copy and configure environment
cp .env.example .env

# Start 1 master + 6 workers (default)
docker compose -f docker/docker-compose.yml up --scale worker=6

# Scale to 8 workers for 120–160 user capacity
docker compose -f docker/docker-compose.yml up --scale worker=8

# Headless / CI run
docker compose -f docker/docker-compose.yml run --rm master \
  locust --master --headless \
    -f perf/locustfile.py \
    --users 100 \
    --expect-workers 6 \
    -H $BASE_URL \
    --run-time 120m \
    --csv /app/artifacts/run
```

---

## Metrics Collected

Every `event(user, "UI_<name>")` call produces a named row in the report:

| Metric | Description |
|--------|-------------|
| `failure_rate_pct` | % of requests that raised an exception |
| `avg_ms` | Mean response time in ms |
| `median_ms` | 50th percentile |
| `max_ms` | Maximum observed |
| `p90_ms` | 90th percentile |
| `p95_ms` | 95th percentile |
| `p99_ms` | 99th percentile |

Reports are per **page**, per **action**, per **workflow**, and as an `__AGGREGATE__` row.
Output to `artifacts/report_<timestamp>_<node>.json` and `.csv`.

---

## UI Event Names

All event names follow the mandatory `UI_<Verb>_<Page/Action>` pattern:

```
UI_Login_Auth0
UI_Open_Programs_Page
UI_Filter_Programs_My_Projects
UI_Filter_Programs_All_Projects
UI_Search_Programs_Query
UI_Clear_Programs_Search
UI_Open_DX_Differential_Expression_Page
UI_Navigate_To_Inventory_Page
UI_Expand_Inventory_Disease_Biology
UI_Open_Inventory_Item_Target_Expression
UI_Open_Inventory_Item_Target_Regulation
UI_Open_Inventory_Item_Cell_Abundance
UI_Open_Inventory_Item_Disease_Severity
UI_Open_Inventory_Item_SOC_Treatment
UI_Load_DX_Disease_Model_ASTH
UI_Select_DX_White_Space_Analysis
UI_Select_DX_Target_Signature_Analysis
UI_Browse_DX_Filter_Bronchus
UI_Browse_DX_Filter_Disease_Vs_Control
UI_Browse_DX_Filter_Fluticasone
UI_Browse_DX_Filter_Week1_500ug
UI_Switch_DX_Disease_Model_COPD
UI_Navigate_To_Inventory_Page_COPD
UI_Open_Inventory_Item_Target_Expression_COPD
UI_Switch_DX_Disease_Model_UC
UI_Navigate_To_Inventory_Page_UC
UI_Open_Inventory_Item_Target_Expression_UC
UI_Open_CytoPedia_Page
UI_Filter_CytoPedia_Entities_Category
UI_Search_CytoPedia_Terms
UI_Open_CytoPedia_Cell_Entities
```

---

## Load Profile (TEST_PROFILE=load)

| Phase | Duration | Users |
|-------|----------|-------|
| Warm-up ramp | 10 min | 0 → 25% |
| Hold 25% | 10 min | 25% |
| Ramp to 50% | 10 min | 25% → 50% |
| Hold 50% | 10 min | 50% |
| Ramp to 75% | 10 min | 50% → 75% |
| Hold 75% | 10 min | 75% |
| Steady state | 30 min | 100% |
| Over-peak | 15 min | 125% |
| Cool-down | 10 min | 125% → 0 |

**Total: ~115 minutes**

---

## Stress Profile (TEST_PROFILE=stress)

10-user steps every 5 min ramp + 5 min hold:

| Phase | Duration | Users |
|-------|----------|-------|
| Step 1 ramp + hold | 10 min | 0 → 10 |
| Step 2 ramp + hold | 10 min | 10 → 20 |
| … | … | … |
| Step 10 ramp | 5 min | 90 → 100 |
| Peak observation | 30 min | 100 |
| Recovery | 20 min | 100 → 0 |

**Total: ~145 minutes** — stop early when stress point is identified.

---

## Worker Sizing Guide

| Workers | Max Concurrent Users | Recommended Node Spec |
|---------|---------------------|----------------------|
| 1 | 15–20 | 4 CPU / 8 GB RAM |
| 3 | 45–60 | 4 CPU / 8 GB × 3 |
| 6 | 90–120 | 4 CPU / 8 GB × 6 |
| 8 | 120–160 | 4 CPU / 8 GB × 8 |

Worker health (CPU, RAM, file descriptors) is logged every 60 seconds.
If CPU exceeds 90% or RAM exceeds 90%, a CRITICAL log entry is emitted.

---

## Flow Discovery Summary

| Flow | URL / Path | Validated Via |
|------|-----------|---------------|
| Auth0 Login | Auth0 redirect | Real staging interaction |
| Programs / Projects | `/programs` | Real staging interaction |
| Disease Explorer DX | `/disease-explorer/differential-expression` | Real staging interaction |
| Inventory (via DX nav) | DX side-nav → Inventory | Real staging interaction |
| CytoPedia | `/cytopedia` | Real staging interaction |

---

## Selector Strategy Summary

| Selector | Strategy | Validated |
|----------|----------|-----------|
| Programs search box | `get_by_role("textbox", name="Search program, project or model...")` | Yes |
| My Projects button | `get_by_role("button", name="My Projects")` | Yes |
| ASTH model combobox | `get_by_role("combobox", name="ASTH Disease Model Asthma")` | Yes |
| Inventory side-nav link | `get_by_role("link", name="Inventory")` | Yes |
| Disease Biology button | `get_by_role("button", name="Disease Biology")` | Yes |
| Inventory item links | `get_by_role("link", name="1 . Target Expression in Disease")` | Yes |
| CytoPedia search box | `get_by_role("textbox", name="Search terms by title or description")` | Yes |
| CytoPedia Entities btn | `get_by_role("button", name="Entities", exact=True).first` | Yes |
| Auth0 email | `get_by_label("Email address *")` | Yes |
| Auth0 password | `get_by_label("Password *")` | Yes |
| Continue button | `get_by_role("button", name="Continue", exact=True)` | Yes |

Run `pytest -m selector` before every load/stress run to re-validate.
