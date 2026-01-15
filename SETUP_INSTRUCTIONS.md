# Setup Instructions

## Quick Start

Follow these steps to set up and run the load testing framework:

### 1. Prerequisites

Ensure you have the following installed and configured:

- **Python 3.8+**
- **gcloud CLI** - Authenticated with the `cytoreason` GCP project
- **kubectl** - Access to the `infra-platform-v2` Kubernetes cluster
- **Git**

### 2. Authenticate with GCP

```bash
# Login to Google Cloud
gcloud auth login

# Set the project
gcloud config set project cytoreason

# Get cluster credentials
gcloud container clusters get-credentials infra-platform-v2 \
  --zone europe-west1-b \
  --project cytoreason
```

### 3. Retrieve Authentication Credentials

Run the setup script to retrieve Auth0 credentials from Kubernetes:

```bash
./setup.sh
```

This script will:
- Connect to the Kubernetes cluster
- Retrieve Auth0 secrets (CLIENT_ID, CLIENT_SECRET, etc.)
- Create a `.env` file with all credentials
- Save Google Cloud service account credentials to `keys/credentials.json`

**Expected output:**
```
*** Setting up kubectl context ***
Fetching cluster endpoint and auth data.
kubeconfig entry generated for infra-platform-v2.
Retrieving secrets from infra-platform-v2...
```

### 4. Verify Credentials

Check that the `.env` file was created with credentials:

```bash
# Should show CLIENT_ID and CLIENT_SECRET
cat .env | grep "CLIENT_"
```

**Example output:**
```
CLIENT_ID=jZlg9JCACK3LI0i3sAnYM7MBhOrC8w1f
CLIENT_SECRET=<secret_value>
```

### 5. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 6. Run Load Tests

#### Option A: Using Locust Web UI

```bash
locust -f locustfile.py --host https://apps.private.cytoreason.com/platform/customers/pxx/
```

Then open http://localhost:8089 in your browser.

#### Option B: Using Locust CLI (Headless)

```bash
# Basic load test
locust -f locustfile.py \
    --host https://apps.private.cytoreason.com/platform/customers/pxx/ \
    --users 10 \
    --spawn-rate 2 \
    --run-time 60s \
    --headless \
    --html reports/report.html
```

#### Option C: Using the Helper Script

```bash
# Run smoke test
./run_tests.sh smoke

# Run full load test
./run_tests.sh load --users 20 --run-time 120s

# Run stress test
./run_tests.sh stress --users 100 --run-time 300s
```

#### Option D: Using Pytest

```bash
# Run smoke tests
pytest tests/ -m smoke

# Run load tests with HTML report
pytest tests/ -m load --html=reports/pytest_report.html
```

## What setup.sh Does

The `setup.sh` script retrieves the following credentials from Kubernetes:

### PXX Customer (Primary Target)
- `CLIENT_ID`: jZlg9JCACK3LI0i3sAnYM7MBhOrC8w1f
- `CLIENT_SECRET`: Retrieved from K8s secret
- `AUTH0_PXX_DOMAIN`: cytoreason-pxx.us.auth0.com

### PYY Customer
- `AUTH0_PYY_CLIENT_ID_UNITTEST1ROLE`
- `AUTH0_PYY_CLIENT_SECRET_UNITTEST1ROLE`
- `AUTH0_PYY_DOMAIN`: cytoreason-pyy.eu.auth0.com

### Machine-to-Machine Credentials
- M2M Public, P01, P13 scope credentials
- CPS API credentials

### Google Cloud
- Service account credentials saved to `keys/credentials.json`

## Authentication Flow

The framework uses **Auth0 OAuth2 Client Credentials Flow**:

1. Framework reads CLIENT_ID and CLIENT_SECRET from `.env`
2. Requests access token from Auth0:
   ```
   POST https://cytoreason-pxx.us.auth0.com/oauth/token
   ```
3. Receives JWT access token valid for 24 hours
4. Includes token in all API requests:
   ```
   Authorization: Bearer <token>
   ```
5. Automatically refreshes token when expired

## Troubleshooting

### setup.sh fails with "gcloud not found"

Install gcloud CLI:
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init
```

### setup.sh fails with kubectl permission errors

Verify you have access to the cluster:
```bash
kubectl get secrets -n default
```

If you don't have access, contact DevOps for permissions.

### .env file is empty or missing CLIENT_SECRET

1. Check Kubernetes access:
   ```bash
   kubectl -n default get secret dps-data-api-test-secrets
   ```

2. Verify the secret exists:
   ```bash
   kubectl -n default get secret dps-data-api-test-secrets -o yaml
   ```

3. If secret doesn't exist, contact DevOps.

### Load tests fail with 401 Unauthorized

Possible causes:
1. CLIENT_SECRET is incorrect or expired
2. Auth0 credentials need to be refreshed
3. Token audience is wrong

Solutions:
1. Re-run `./setup.sh` to get fresh credentials
2. Verify credentials in Auth0 dashboard
3. Check that BASE_URL matches the Auth0 audience

### Connection timeouts or DNS resolution errors

The target URL may require VPN or specific network access. Ensure you're connected to the Cytoreason network.

## Environment Variables Reference

After running `setup.sh`, your `.env` file will contain:

| Variable | Description | Example |
|----------|-------------|---------|
| `CLIENT_ID` | Auth0 client ID | jZlg9JCACK3LI0i3sAnYM7MBhOrC8w1f |
| `CLIENT_SECRET` | Auth0 client secret | <retrieved from K8s> |
| `AUTH0_PXX_DOMAIN` | Auth0 domain for PXX | cytoreason-pxx.us.auth0.com |
| `AUTH0_AUDIENCE` | API audience | https://apps.private.cytoreason.com/ |
| `BASE_URL` | Target application URL | https://apps.private.cytoreason.com/platform/customers/pxx/ |
| `USERS` | Number of simulated users | 10 |
| `SPAWN_RATE` | Rate of user spawning | 1 |
| `RUN_TIME` | Test duration | 60s |
| `LOG_LEVEL` | Logging verbosity | INFO |
| `GOOGLE_APPLICATION_CREDENTIALS` | GCP service account key | ./keys/credentials.json |

## Security Notes

1. **Never commit `.env` file** - Contains sensitive credentials
2. **Never commit `keys/` directory** - Contains Google Cloud credentials
3. **Rotate secrets regularly** - Contact DevOps for credential rotation
4. **Limit access** - Only authorized personnel should run setup.sh

## Next Steps

After successful setup:

1. **Review test scenarios** in `locust_tests/locustfiles/example_test.py`
2. **Customize tests** for your specific use cases
3. **Run baseline tests** to establish performance benchmarks
4. **Set up CI/CD** integration for automated testing
5. **Monitor results** and adjust test parameters as needed

## Support

For issues or questions:
- Check [AUTH_CREDENTIALS_GUIDE.md](AUTH_CREDENTIALS_GUIDE.md) for detailed credential information
- Contact DevOps for GCP/K8s access issues
- Contact QA team for test framework questions
- Check Auth0 dashboard for application status
