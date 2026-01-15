# Authentication Credentials Guide

This document outlines all authentication credentials required for the load testing framework.

## Overview

The Cytoreason platform uses **Auth0** for authentication with OAuth2 client credentials flow. The `setup.sh` script retrieves all necessary secrets from Kubernetes and stores them in the `.env` file.

## Prerequisites

Before running `setup.sh`, you need:

1. **gcloud CLI** - Authenticated with the `cytoreason` GCP project
2. **kubectl** - Access to the `infra-platform-v2` Kubernetes cluster
3. **Permissions** - Access to read secrets from Kubernetes namespaces

## Setup Process

Run the setup script to retrieve credentials:

```bash
./setup.sh
```

This will:
- Create a `keys/` directory for storing credentials
- Retrieve Auth0 secrets from Kubernetes
- Generate a `.env` file with all required credentials
- Save Google Cloud service account credentials to `keys/credentials.json`

## Credentials Retrieved

### 1. PXX Customer Credentials (Primary Target)

Used for testing `https://apps.private.cytoreason.com/platform/customers/pxx/`

| Variable | Value | Source |
|----------|-------|--------|
| `CLIENT_ID` | `jZlg9JCACK3LI0i3sAnYM7MBhOrC8w1f` | Hardcoded |
| `CLIENT_SECRET` | Retrieved from K8s | `dps-data-api-test-secrets` → `AUTH0_PXX_CLIENT_SECRET_UNITTEST1VIEW` |
| `AUTH0_PXX_CLIENT_ID_UNITTEST1ROLE` | `jZlg9JCACK3LI0i3sAnYM7MBhOrC8w1f` | Hardcoded |
| `AUTH0_PXX_CLIENT_SECRET_UNITTEST1ROLE` | Retrieved from K8s | `dps-data-api-test-secrets` → `AUTH0_PXX_CLIENT_SECRET_UNITTEST1VIEW` |
| `AUTH0_PXX_DOMAIN` | `cytoreason-pxx.us.auth0.com` | Hardcoded |
| `PXX_ROLE` | `biologist` | Hardcoded |

**Auth0 Token Endpoint:**
```
https://cytoreason-pxx.us.auth0.com/oauth/token
```

### 2. PYY Customer Credentials

Used for testing PYY customer environment.

| Variable | Value | Source |
|----------|-------|--------|
| `AUTH0_PYY_CLIENT_ID_UNITTEST1ROLE` | `LgpR6QQnk15S4dSeQmPVhiyDVHRiQKnp` | Hardcoded |
| `AUTH0_PYY_CLIENT_SECRET_UNITTEST1ROLE` | Retrieved from K8s | `dps-data-api-test-secrets` → `AUTH0_PYY_CLIENT_SECRET_UNITTEST1ROLE` |
| `AUTH0_PYY_DOMAIN` | `cytoreason-pyy.eu.auth0.com` | Hardcoded |
| `PYY_ROLE` | `automation-biologist` | Hardcoded |

**Auth0 Token Endpoint:**
```
https://cytoreason-pyy.eu.auth0.com/oauth/token
```

### 3. Machine-to-Machine (M2M) Credentials

#### M2M Public Scope
| Variable | Value | Source |
|----------|-------|--------|
| `CLIENT_ID_M2M_PUBLIC` | `18O0q92Yve0Hy74gypPvtcEmuP7Tv8MM` | Hardcoded |
| `CLIENT_SECRET_M2M_PUBLIC` | Retrieved from K8s | `m2m-secrets` → `CLIENT_SECRET_M2M_ALL_SCOPES` |
| `CLIENT_ID_M2M_PUBLIC_SCOPE` | `18O0q92Yve0Hy74gypPvtcEmuP7Tv8MM` | Hardcoded |
| `CLIENT_SECRET_M2M_PUBLIC_SCOPE` | Retrieved from K8s | `m2m-secrets` → `CLIENT_SECRET_M2M_ALL_SCOPES` |

#### M2M P01 Customer Scope
| Variable | Value | Source |
|----------|-------|--------|
| `CLIENT_ID_M2M_P01_SCOPE` | `3mVWmGlTEH9HKu0agRUyh4rB1CH30Xwj` | Hardcoded |
| `CLIENT_SECRET_M2M_P01_SCOPE` | Retrieved from K8s | `storage-secrets` → `CLIENT_SECRET_p01` |

#### M2M P13 Customer Scope
| Variable | Value | Source |
|----------|-------|--------|
| `CLIENT_ID_M2M_P13_SCOPE` | `MwpME8GiqQS98BwbKcp4BumU5peHyvcZ` | Hardcoded |
| `CLIENT_SECRET_M2M_P13_SCOPE` | Retrieved from K8s | `storage-secrets` → `CLIENT_SECRET_p13` |

### 4. CPS API Credentials

| Variable | Value | Source |
|----------|-------|--------|
| `AUTH0_CLIENT_ID_M2M_CPS_API` | `UzMf5nd2hySFm3N5YDxNgqKupcbqFCwM` | Hardcoded |
| `AUTH0_CLIENT_SECRET_M2M_CPS_API` | Retrieved from K8s | `dps-data-api-test-secrets` → `CLIENT_SECRET_M2M_CPS_API` |

### 5. Google Cloud Credentials

| Variable | Value | Source |
|----------|-------|--------|
| `GOOGLE_APPLICATION_CREDENTIALS` | `./keys/credentials.json` | Retrieved from K8s secret `automation-framework-sa-creds` |
| `PROJECT_ID` | `cytoreason` | Hardcoded |

### 6. API Endpoints

| Variable | Value |
|----------|-------|
| `CYTO_CC_BASE_URL` | `https://cyto-cc.cytoreason.com` |
| `CYTO_CC_API_PATH` | `/api/v1` |

### 7. Other Configuration

| Variable | Value |
|----------|-------|
| `CLIENT` | `Machine` |
| `PIP_INDEX_URL` | `https://europe-west1-python.pkg.dev/cytoreason/cytoreason-python-all/simple/` |
| `ARTIFACTS_DIR` | `/ARTIFACTS` |
| `COMM_DIR` | `/COMMUNICATION` |
| `UID` | Current user ID |
| `GID` | Current group ID |

## Missing Credentials Check

After running `setup.sh`, verify that `.env` contains all required credentials:

```bash
# Check if .env file exists and has content
cat .env

# Required for PXX load testing:
grep "CLIENT_ID=" .env
grep "CLIENT_SECRET=" .env
grep "AUTH0_PXX_DOMAIN=" .env
```

## Auth0 OAuth2 Flow

The framework uses **Client Credentials Flow** for machine-to-machine authentication:

### Token Request

```bash
curl --request POST \
  --url https://cytoreason-pxx.us.auth0.com/oauth/token \
  --header 'content-type: application/json' \
  --data '{
    "client_id": "jZlg9JCACK3LI0i3sAnYM7MBhOrC8w1f",
    "client_secret": "YOUR_CLIENT_SECRET",
    "audience": "https://apps.private.cytoreason.com/",
    "grant_type": "client_credentials"
  }'
```

### Token Response

```json
{
  "access_token": "eyJhbGci...token...",
  "token_type": "Bearer",
  "expires_in": 86400
}
```

### Using the Token

Include the access token in the Authorization header:

```
Authorization: Bearer eyJhbGci...token...
```

## Troubleshooting

### Issue: setup.sh fails with "gcloud not found"

**Solution:** Install and configure gcloud CLI:
```bash
# Install gcloud
curl https://sdk.cloud.google.com | bash

# Authenticate
gcloud auth login

# Set project
gcloud config set project cytoreason
```

### Issue: setup.sh fails with kubectl errors

**Solution:** Verify kubectl access:
```bash
# Get cluster credentials
gcloud container clusters get-credentials infra-platform-v2 \
  --zone europe-west1-b \
  --project cytoreason

# Test access
kubectl get secrets -n default
```

### Issue: CLIENT_SECRET is empty in .env

**Possible causes:**
1. Insufficient permissions to read K8s secrets
2. Secret doesn't exist in the cluster
3. Incorrect secret name or key

**Solution:**
```bash
# Manually check if secret exists
kubectl -n default get secret dps-data-api-test-secrets

# Check specific key
kubectl -n default get secret dps-data-api-test-secrets -o yaml
```

### Issue: Auth0 token request fails with 401

**Possible causes:**
1. Invalid CLIENT_SECRET
2. Expired or revoked credentials
3. Incorrect Auth0 domain

**Solution:**
1. Re-run `setup.sh` to refresh credentials
2. Verify CLIENT_ID and CLIENT_SECRET match in Auth0 dashboard
3. Check Auth0 domain is correct

## Security Best Practices

1. **Never commit `.env` file** - It's already in `.gitignore`
2. **Never commit `keys/` directory** - Contains sensitive credentials
3. **Rotate secrets regularly** - Update secrets in Kubernetes
4. **Limit token scope** - Use minimum required permissions
5. **Monitor token usage** - Check Auth0 logs for suspicious activity

## For Load Testing

The framework automatically:
1. Reads credentials from `.env` file
2. Requests Auth0 access token using client credentials
3. Includes token in all API requests
4. Refreshes token when expired

You just need to:
1. Run `./setup.sh` once
2. Run load tests as normal

```bash
# The framework will handle authentication automatically
locust -f locustfile.py --host https://apps.private.cytoreason.com/platform/customers/pxx/
```

## Quick Start

```bash
# 1. Run setup to get credentials
./setup.sh

# 2. Verify credentials
cat .env | grep CLIENT_ID

# 3. Run load test
./run_tests.sh load --users 10 --run-time 60s
```

## Support

If you encounter issues:
1. Check this guide for troubleshooting steps
2. Verify your GCP and K8s permissions
3. Contact the DevOps team for credential access
4. Check Auth0 dashboard for application status
