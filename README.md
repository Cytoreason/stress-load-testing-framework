# CytoReason Platform Load Testing

Load testing framework for the CytoReason platform using Locust.

## Quick Start

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Copy config template and add your token
cp locust_tests/config/config.yaml.example locust_tests/config/config.yaml
# Edit config.yaml and paste your Bearer token

# 3. Run the UI flow test
locust -f locustfile_ui_flow.py --host https://apps.private.cytoreason.com --web-port 8090

# 4. Open browser to http://localhost:8090
```

## Project Structure

```
├── locustfile_ui_flow.py          # Main entry point
├── locust_tests/
│   ├── config/
│   │   └── config.yaml            # Configuration (Bearer token here)
│   ├── locustfiles/
│   │   └── ui_flow_test.py        # UI flow test implementation
│   └── utils/
│       └── logger.py              # Logging utility
├── requirements.txt               # Python dependencies
└── _archive/                      # Old/unused files
```

## Configuration

### Bearer Token

The test requires a valid Bearer token. To configure:

1. Login to https://apps.private.cytoreason.com/platform/customers/pyy/
2. Open DevTools (F12) → Network tab
3. Filter by `api.platform.private`
4. Click any request → Headers → Copy `Authorization: Bearer eyJ...`
5. Paste the token (without "Bearer " prefix) in `locust_tests/config/config.yaml`:

```yaml
auth:
  bearer_token: "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIs..."
```

⚠️ Tokens expire after ~24 hours. Get a new one if you see 401 errors.

## Test Steps (ST-01 to ST-15)

The UI flow test simulates real user journeys:

| Step | Description | Endpoint |
|------|-------------|----------|
| ST-01 | Landing + Auth | `/admin/tenant` |
| ST-02 | Project Catalog | `/project/fetch/catalog` |
| ST-03 | Question Index | `resourceType=question_index` |
| ST-04 | Gene Data | `resourceType=gene` |
| ST-05 | Disease Explorer | Page navigation |
| ST-06 | Meta Contexts | `resourceType=meta_contexts_datasets_map` |
| ST-07 | Gene Expr Meta | `resourceType=gene_expression_differences_meta` |
| ST-08 | Gene Expression | `resourceType=gene_expression_differences` |
| ST-09 | Cell Abundance | `resourceType=cell_abundance_differences` |
| ST-10 | Geneset Grouped | `resourceType=geneset_grouped` |
| ST-11 | Geneset Regulation | `resourceType=geneset_expression_regulation_differences` |
| ST-12 | Target-Cell Page | Page navigation |
| ST-13 | Cell Abundance Meta | `resourceType=cell_abundance_differences_meta` |
| ST-14 | Switch Disease | Switch between diseases |
| ST-15 | Return to Landing | Complete journey |

## Load Pattern

The test uses a custom LoadTestShape:

```
0 → 5 users    over 2 min   (warm up)
Hold at 5      for 5 min
5 → 20 users   over 5 min
Hold at 20     for 10 min
20 → 50 users  over 10 min
Hold at 50     for 15 min
50 → 0 users   over 3 min   (ramp down)

Total: ~50 minutes
```

## Diseases Tested

- Ulcerative Colitis (colon)
- Crohn's Disease (colon)
- Celiac Disease (duodenum)
- Systemic Sclerosis (skin)

## Running Without UI

```bash
# Run headless with specific user count and duration
locust -f locustfile_ui_flow.py \
  --host https://apps.private.cytoreason.com \
  --headless \
  --users 10 \
  --spawn-rate 1 \
  --run-time 5m \
  --csv=results
```

## Results

After running, check:
- `results_stats.csv` - Request statistics
- `results_failures.csv` - Failed requests
- Locust web UI charts for real-time monitoring

## Adding New Tests

### 1. Create a New Test File

Create a new file in `locust_tests/locustfiles/`, e.g., `my_new_test.py`:

```python
from locust import HttpUser, task, between, SequentialTaskSet
from locust_tests.utils.logger import setup_logger
import random
import time
import yaml
import os

logger = setup_logger()

# Load Bearer token from config
BEARER_TOKEN = None
try:
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        BEARER_TOKEN = config.get('auth', {}).get('bearer_token')
except Exception as e:
    logger.warning(f"Could not load bearer token: {e}")


class MyTaskSet(SequentialTaskSet):
    """Sequential user journey - tasks execute in order"""
    
    def on_start(self):
        """Initialize user session (runs once per user)"""
        self.auth_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if BEARER_TOKEN:
            self.auth_headers["Authorization"] = f"Bearer {BEARER_TOKEN}"
    
    @task
    def step_01_example(self):
        """First step in the journey"""
        with self.client.get("/api/endpoint", name="ST-01: Example", 
                            headers=self.auth_headers, catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"Failed: {r.status_code}")
        
        time.sleep(random.uniform(0.5, 1))  # Think time
    
    @task
    def step_02_post_example(self):
        """Second step - POST request"""
        payload = {"key": "value"}
        
        with self.client.post("/api/another", name="ST-02: Post Example",
                             json=payload, headers=self.auth_headers, 
                             catch_response=True) as r:
            if r.status_code in [200, 201]:
                r.success()
            else:
                r.failure(f"Failed: {r.status_code}")
        
        time.sleep(random.uniform(1, 2))


class MyNewUser(HttpUser):
    """User class - Locust spawns instances of this"""
    tasks = [MyTaskSet]
    wait_time = between(1, 3)  # Wait between task iterations
    host = "https://your-api-host.com"
```

### 2. Create an Entry Point File

Create a new entry point in the project root, e.g., `locustfile_my_test.py`:

```python
from locust import LoadTestShape
from locust_tests.locustfiles.my_new_test import MyNewUser

__all__ = ['MyNewUser']

# Optional: Add a custom load shape
class MyTestShape(LoadTestShape):
    """Custom load pattern"""
    
    stages = [
        {"duration": 60, "users": 5, "spawn_rate": 1},    # Ramp to 5
        {"duration": 180, "users": 5, "spawn_rate": 1},   # Hold at 5
        {"duration": 300, "users": 10, "spawn_rate": 1},  # Ramp to 10
    ]
    
    def tick(self):
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])
        return None  # Stop test
```

### 3. Run Your Test

```bash
# With web UI
locust -f locustfile_my_test.py --host https://your-api-host.com --web-port 8090

# Headless mode
locust -f locustfile_my_test.py --host https://your-api-host.com \
  --headless --users 5 --spawn-rate 1 --run-time 5m
```

### Key Patterns

| Pattern | Use Case |
|---------|----------|
| `SequentialTaskSet` | Steps execute in order (user journeys) |
| `TaskSet` | Steps execute randomly based on weight |
| `@task(weight)` | Higher weight = more frequent execution |
| `catch_response=True` | Manual pass/fail control |
| `time.sleep()` | Simulate user think time |

### Tips

- **Capture HAR files**: Use browser DevTools to record real API calls, then replicate them
- **Use `name` parameter**: Group similar requests under one name in reports
- **Handle auth failures**: Check for 401/403 and fail gracefully
- **Add think time**: Use `time.sleep(random.uniform(min, max))` between steps
- **Log important events**: Use the logger for debugging
