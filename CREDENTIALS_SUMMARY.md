# Authentication Credentials Summary

## Overview

This document summarizes all authentication credentials required by the load testing framework, based on the `setup.sh` script analysis.

## ✅ Credentials Retrieved by setup.sh

The following credentials are **automatically retrieved** from Kubernetes when you run `./setup.sh`:

### 1. Primary Credentials (PXX Customer)

| Credential | Hardcoded Value | Retrieved from K8s | Used For |
|------------|-----------------|-------------------|----------|
| `CLIENT_ID` | `jZlg9JCACK3LI0i3sAnYM7MBhOrC8w1f` | No | Default client ID for load tests |
| `CLIENT_SECRET` | - | ✅ Yes (`dps-data-api-test-secrets` → `AUTH0_PXX_CLIENT_SECRET_UNITTEST1VIEW`) | Auth0 authentication |
| `AUTH0_PXX_CLIENT_ID_UNITTEST1ROLE` | `jZlg9JCACK3LI0i3sAnYM7MBhOrC8w1f` | No | PXX specific client ID |
| `AUTH0_PXX_CLIENT_SECRET_UNITTEST1ROLE` | - | ✅ Yes (`dps-data-api-test-secrets` → `AUTH0_PXX_CLIENT_SECRET_UNITTEST1VIEW`) | PXX authentication |
| `AUTH0_PXX_DOMAIN` | `cytoreason-pxx.us.auth0.com` | No | Auth0 domain for PXX |
| `PXX_ROLE` | `biologist` | No | User role |

### 2. PYY Customer Credentials

| Credential | Hardcoded Value | Retrieved from K8s | Used For |
|------------|-----------------|-------------------|----------|
| `AUTH0_PYY_CLIENT_ID_UNITTEST1ROLE` | `LgpR6QQnk15S4dSeQmPVhiyDVHRiQKnp` | No | PYY client ID |
| `AUTH0_PYY_CLIENT_SECRET_UNITTEST1ROLE` | - | ✅ Yes (`dps-data-api-test-secrets` → `AUTH0_PYY_CLIENT_SECRET_UNITTEST1ROLE`) | PYY authentication |
| `AUTH0_PYY_DOMAIN` | `cytoreason-pyy.eu.auth0.com` | No | Auth0 domain for PYY |
| `PYY_ROLE` | `automation-biologist` | No | User role |

### 3. Machine-to-Machine (M2M) Credentials

#### M2M Public Scope
| Credential | Hardcoded Value | Retrieved from K8s | Used For |
|------------|-----------------|-------------------|----------|
| `CLIENT_ID_M2M_PUBLIC` | `18O0q92Yve0Hy74gypPvtcEmuP7Tv8MM` | No | M2M public client ID |
| `CLIENT_SECRET_M2M_PUBLIC` | - | ✅ Yes (`m2m-secrets` → `CLIENT_SECRET_M2M_ALL_SCOPES`) | M2M authentication |
| `CLIENT_ID_M2M_PUBLIC_SCOPE` | `18O0q92Yve0Hy74gypPvtcEmuP7Tv8MM` | No | Same as above |
| `CLIENT_SECRET_M2M_PUBLIC_SCOPE` | - | ✅ Yes (`m2m-secrets` → `CLIENT_SECRET_M2M_ALL_SCOPES`) | M2M authentication |

#### M2M P01 Customer Scope
| Credential | Hardcoded Value | Retrieved from K8s | Used For |
|------------|-----------------|-------------------|----------|
| `CLIENT_ID_M2M_P01_SCOPE` | `3mVWmGlTEH9HKu0agRUyh4rB1CH30Xwj` | No | P01 customer M2M |
| `CLIENT_SECRET_M2M_P01_SCOPE` | - | ✅ Yes (`storage-secrets` → `CLIENT_SECRET_p01`) | P01 authentication |

#### M2M P13 Customer Scope
| Credential | Hardcoded Value | Retrieved from K8s | Used For |
|------------|-----------------|-------------------|----------|
| `CLIENT_ID_M2M_P13_SCOPE` | `MwpME8GiqQS98BwbKcp4BumU5peHyvcZ` | No | P13 customer M2M |
| `CLIENT_SECRET_M2M_P13_SCOPE` | - | ✅ Yes (`storage-secrets` → `CLIENT_SECRET_p13`) | P13 authentication |

### 4. CPS API Credentials

| Credential | Hardcoded Value | Retrieved from K8s | Used For |
|------------|-----------------|-------------------|----------|
| `AUTH0_CLIENT_ID_M2M_CPS_API` | `UzMf5nd2hySFm3N5YDxNgqKupcbqFCwM` | No | CPS API client ID |
| `AUTH0_CLIENT_SECRET_M2M_CPS_API` | - | ✅ Yes (`dps-data-api-test-secrets` → `CLIENT_SECRET_M2M_CPS_API`) | CPS API auth |

### 5. Google Cloud Credentials

| Credential | Retrieved from K8s | Saved To | Used For |
|------------|-------------------|----------|----------|
| `GOOGLE_APPLICATION_CREDENTIALS` | ✅ Yes (`automation-framework-sa-creds` → `automation-framework.json`) | `./keys/credentials.json` | GCP service account |

### 6. API Configuration

| Variable | Value | Used For |
|----------|-------|----------|
| `CYTO_CC_BASE_URL` | `https://cyto-cc.cytoreason.com` | Cytoreason API base URL |
| `CYTO_CC_API_PATH` | `/api/v1` | API path |
| `PIP_INDEX_URL` | `https://europe-west1-python.pkg.dev/cytoreason/cytoreason-python-all/simple/` | Python package index |

## ❌ Missing/Empty Credentials (Before Running setup.sh)

Before running `setup.sh`, the following credentials will be **missing or empty** in `.env`:

1. ❌ `CLIENT_SECRET` - **REQUIRED for load testing**
2. ❌ `AUTH0_PXX_CLIENT_SECRET_UNITTEST1ROLE` - PXX authentication
3. ❌ `AUTH0_PYY_CLIENT_SECRET_UNITTEST1ROLE` - PYY authentication
4. ❌ `CLIENT_SECRET_M2M_PUBLIC` - M2M public scope
5. ❌ `CLIENT_SECRET_M2M_P01_SCOPE` - P01 customer scope
6. ❌ `CLIENT_SECRET_M2M_P13_SCOPE` - P13 customer scope
7. ❌ `AUTH0_CLIENT_SECRET_M2M_CPS_API` - CPS API
8. ❌ `GOOGLE_APPLICATION_CREDENTIALS` file - GCP service account

## ⚠️ What You Need to Run setup.sh

To retrieve these missing credentials, you need:

### Prerequisites

1. **gcloud CLI** - Installed and authenticated
   ```bash
   gcloud auth login
   gcloud config set project cytoreason
   ```

2. **kubectl** - Configured for the `infra-platform-v2` cluster
   ```bash
   gcloud container clusters get-credentials infra-platform-v2 \
     --zone europe-west1-b --project cytoreason
   ```

3. **Kubernetes Permissions** - Read access to the following secrets:
   - `default` namespace:
     - `automation-framework-sa-creds`
     - `m2m-secrets`
     - `dps-data-api-test-secrets`
   - `apps` namespace:
     - `storage-secrets`

## 🔒 Security Note

**All secret values are retrieved from Kubernetes and stored in `.env`**, which is in `.gitignore` and should NEVER be committed to git.

The following secrets are retrieved:
- **5 client secrets** from Auth0 (for different scopes/customers)
- **1 Google Cloud service account** JSON key file

## 📋 Quick Check: Do I Have All Credentials?

After running `./setup.sh`, verify you have credentials:

```bash
# Check if .env has the required variables
cat .env | grep -E "CLIENT_ID|CLIENT_SECRET|AUTH0.*DOMAIN"
```

**Expected output:**
```
CLIENT_ID=jZlg9JCACK3LI0i3sAnYM7MBhOrC8w1f
CLIENT_SECRET=<some_long_secret_value>
AUTH0_PXX_DOMAIN=cytoreason-pxx.us.auth0.com
AUTH0_PYY_DOMAIN=cytoreason-pyy.eu.auth0.com
```

**If CLIENT_SECRET is empty**, you need to:
1. Check your Kubernetes access
2. Verify the secret exists in K8s
3. Contact DevOps for help

## 🚀 Next Steps

1. **Run setup.sh**:
   ```bash
   ./setup.sh
   ```

2. **Verify credentials**:
   ```bash
   cat .env | grep CLIENT_SECRET
   ```

3. **Run load tests**:
   ```bash
   locust -f locustfile.py --host https://apps.private.cytoreason.com/platform/customers/pxx/
   ```

## 📚 Additional Documentation

- [AUTH_CREDENTIALS_GUIDE.md](AUTH_CREDENTIALS_GUIDE.md) - Detailed credential information
- [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md) - Step-by-step setup guide
- [README.md](README.md) - Framework overview and usage

## 🆘 Need Help?

- **Can't run setup.sh?** → Check [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md#troubleshooting)
- **Auth0 errors?** → See [AUTH_CREDENTIALS_GUIDE.md](AUTH_CREDENTIALS_GUIDE.md#troubleshooting)
- **K8s permission denied?** → Contact DevOps team
- **General questions?** → Check README.md
