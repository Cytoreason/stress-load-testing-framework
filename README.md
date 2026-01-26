# CytoReason Platform - Hybrid Load Testing Framework

A comprehensive load testing framework combining **Locust** for high-throughput API stress testing with **Playwright** for real browser-based UI performance measurement.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HYBRID LOAD TESTING                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│    ┌──────────────────────────────────────────────────────────────────┐     │
│    │                       LOCUST MASTER                               │     │
│    │                   http://localhost:8089                           │     │
│    │                                                                   │     │
│    │   ┌─────────────────────────────────────────────────────────┐    │     │
│    │   │           StagedLoadShape Controller                     │    │     │
│    │   │   • 7-stage ramp pattern (0→10→50→100→0)                │    │     │
│    │   │   • 56-minute total duration                             │    │     │
│    │   │   • Automatic user scaling                               │    │     │
│    │   └─────────────────────────────────────────────────────────┘    │     │
│    └───────────────────────────┬──────────────────────────────────────┘     │
│                                │                                             │
│                ┌───────────────┴───────────────┐                            │
│                │                               │                            │
│                ▼                               ▼                            │
│    ┌───────────────────────┐     ┌───────────────────────┐                 │
│    │    API STRESSER       │     │    BROWSER USER       │                 │
│    │   (BackendStresser)   │     │   (PlaywrightUser)    │                 │
│    │                       │     │                       │                 │
│    │ • Pure HTTP requests  │     │ • Real Chromium       │                 │
│    │ • Bearer token auth   │     │ • Auth0 UI login      │                 │
│    │ • 10 API endpoints    │     │ • 5 page flows        │                 │
│    │ • 1s between requests │     │ • 5s between actions  │                 │
│    └───────────┬───────────┘     └───────────┬───────────┘                 │
│                │                              │                             │
│                ▼                              ▼                             │
│    ┌───────────────────────┐     ┌───────────────────────┐                 │
│    │      API GATEWAY      │     │    WEB APPLICATION    │                 │
│    │ api.platform.private  │     │   apps.private        │                 │
│    │ .cytoreason.com       │     │   .cytoreason.com     │                 │
│    └───────────────────────┘     └───────────────────────┘                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Load Engine** | Locust 2.23.1 | Distributed load generation |
| **Browser Automation** | Playwright | Real browser UI testing |
| **Plugin** | locust-plugins | Playwright integration |
| **Runtime** | Python 3.11+ | Framework runtime |
| **Authentication** | Auth0 | OAuth2 Bearer tokens |
| **Containerization** | Docker Compose | Distributed deployment |

## Quick Start

### 1. Setup Environment

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Configure Authentication

```bash
# Set your Auth0 bearer token
export AUTH_TOKEN='Bearer eyJhbG...'
```

### 3. Run the Test

```bash
# Start Locust with staged load shape
locust -f locustfile.py

# Open http://localhost:8089 and click START
# The StagedLoadShape will automatically control the test
```

## Load Test Pattern

The framework uses a **staged ramp pattern** for realistic load testing:

```
Users
  │
100├─────────────────────────────────────────────────────────╮
   │                                              ╭──────────╯
 50├──────────────────────────╮         ╭────────╯
   │              ╭───────────╯─────────╯
 10├──────╮──────╯
   │    ╱
  0├───╯──────────────────────────────────────────────────────╯
   └──┬──┬────┬─────────┬──────────┬───────────────┬──────────┬──
      0  5    6        16         26              41         51  56 min
```

| Stage | Users | Duration | Purpose |
|-------|-------|----------|---------|
| 1 | 0 → 10 | 5 min | Warm Up |
| 2 | Hold 10 | 1 min | Baseline |
| 3 | 10 → 50 | 10 min | Scale Test |
| 4 | Hold 50 | 10 min | Sustained Load |
| 5 | 50 → 100 | 15 min | Peak Ramp |
| 6 | Hold 100 | 10 min | Peak Sustained |
| 7 | 100 → 0 | 5 min | Ramp Down |

**Total Duration: 56 minutes**

## What We Test

### API Endpoints (10 endpoints)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/` | Health Check |
| `GET` | `/v1.0/customer/pyy/e2/platform/admin/tenant` | Authentication |
| `POST` | `/v1.0/customer/pyy/e2/platform/project/fetch/catalog` | Project Catalog |
| `POST` | `/v1.0/customer/pyy/e2/platform/query/fetch?resourceType=question_index` | Question Index |
| `POST` | `/v1.0/customer/pyy/e2/platform/query/fetch?resourceType=gene` | Gene Data |
| `POST` | `/v1.0/customer/pyy/e2/platform/query/fetch?resourceType=meta_contexts_datasets_map` | Meta Contexts |
| `POST` | `/v1.0/customer/pyy/e2/platform/query/fetch?resourceType=gene_expression_differences_meta` | Gene Expression |
| `POST` | `/v1.0/customer/pyy/e2/platform/query/fetch?resourceType=model_diseases` | Disease Models |
| `POST` | `/v1.0/customer/pyy/e2/platform/query/fetch?resourceType=cell_view` | Cell View |
| `POST` | `/v1.0/customer/pyy/e2/platform/query/fetch?resourceType=total_project_counters` | Counters |

### UI Pages (5 browser flows)

| Page | URL | Measurements |
|------|-----|--------------|
| **Landing Page** | `/platform/customers/pyy/` | Full page load, dashboard render |
| **Disease Explorer** | `/platform/customers/pyy/disease-explorer/differential-expression` | Data visualization |
| **Programs** | `/platform/customers/pyy/programs` | Table render time |
| **CytoPedia** | `/platform/customers/pyy/cytopedia` | Search interface |
| **Sidebar Navigation** | `/platform/customers/pyy/` | Navigation responsiveness |

## Project Structure

```
stress-load-testing-framework/
├── locustfile.py              # Main entry point with StagedLoadShape
├── requirements.txt           # Python dependencies
├── docker-compose.yml         # Docker distributed deployment
│
├── scenarios/                 # User scenarios
│   ├── api_user.py           # BackendStresser - API load generation
│   └── ui_user.py            # UIStressUser - Playwright browser testing
│
├── common/                    # Shared utilities
│   ├── config.py             # Configuration management
│   ├── auth_util.py          # Authentication helpers
│   └── data_loader.py        # Test data loading
│
├── pages/                     # Page Object Models (for UI tests)
│   ├── base_page.py          # Base page class
│   ├── login_page.py         # Auth0 login page
│   └── dashboard_page.py     # Dashboard page
│
└── locust_tests/             # Legacy test implementations
    ├── config/
    │   └── config.yaml       # Configuration file
    └── locustfiles/
        ├── base.py           # Base test class
        └── high_load_test.py # High load test
```

## User Distribution

At peak load (100 users), the framework distributes:

```
┌────────────────────────────────────────────────┐
│  Total Users: 100                              │
│  ├── Browser Users: ~83 (weight: 5)            │
│  │   └── RAM: ~25GB (300MB × 83)               │
│  └── API Users: ~17 (weight: 1)                │
│      └── RAM: ~34MB (2MB × 17)                 │
└────────────────────────────────────────────────┘
```

## Running Tests

### Web UI Mode (Recommended)

```bash
# Start Locust server
locust -f locustfile.py

# Open http://localhost:8089 and click START
```

### Headless Mode

```bash
# Run for specific duration
locust -f locustfile.py --headless -t 56m

# Export results to CSV
locust -f locustfile.py --headless -t 56m --csv=results
```

### Docker Distributed Mode

```bash
# Start master + 4 workers
docker-compose up --scale worker=4

# Open http://localhost:8089
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AUTH_TOKEN` | Auth0 Bearer token | Yes |
| `TARGET_BASE_URL` | Web app URL | No (default set) |
| `TARGET_API_URL` | API URL | No (default set) |
| `DEFAULT_USERNAME` | Auth0 email | No (default set) |
| `DEFAULT_PASSWORD` | Auth0 password | No (default set) |

### Default Credentials

```
Username: ui.automation@cytoreason.com
Password: U!a@zMatE
```

### Getting a Bearer Token

1. Login to https://apps.private.cytoreason.com/platform/customers/pyy/
2. Open DevTools (F12) → Network tab
3. Filter by `api.platform.private`
4. Copy the `Authorization: Bearer eyJ...` header value
5. Export: `export AUTH_TOKEN='Bearer eyJ...'`

> **Note:** Tokens expire after ~24 hours

## Test Results

After running, check:

- **Locust Web UI** - Real-time charts at http://localhost:8089
- **CSV Reports** - `results_stats.csv`, `results_failures.csv`
- **HTML Report** - Generated report with full statistics

### Key Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| **Failure Rate** | < 1% | Percentage of failed requests |
| **Median Response** | < 200ms | 50th percentile latency |
| **P95 Response** | < 1s | 95th percentile latency |
| **P99 Response** | < 5s | 99th percentile latency |

## Diseases Tested

The framework tests with these disease contexts:

- Ulcerative Colitis (UC)
- Crohn's Disease (CD)
- Chronic Obstructive Pulmonary Disease (COPD)
- Idiopathic Pulmonary Fibrosis (IPF)
- Atopic Dermatitis (AD)
- Psoriasis (PSO)
- Rheumatoid Arthritis (RA)
- Systemic Lupus Erythematosus (SLE)

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `401 Unauthorized` | Token expired - get a new one |
| `502 Bad Gateway` | Server overloaded - reduce users |
| `Stuck at N users` | Playwright slow to spawn - lower spawn rate |
| `Out of memory` | Too many browser users - reduce browser weight |

### Browser User Memory

Each Playwright browser uses ~300MB RAM. At 100 users with 5:1 ratio:
- 83 browsers × 300MB = **~25GB RAM needed**

For lower memory environments, adjust weights in `locustfile.py`:

```python
class BrowserUser(UIStressUser):
    weight = 1  # Reduce browser proportion

class APIStresser(BackendStresser):
    weight = 10  # Increase API proportion
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests locally
5. Submit a pull request

## License

Internal use only - CytoReason
