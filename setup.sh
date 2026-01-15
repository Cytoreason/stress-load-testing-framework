#!/usr/bin/env bash

### Setup a new development environment for sphere-ui-automation

# Scriptdir is the directory in which this script resides
SCRIPTDIR=$(
  cd -P $(dirname "$0")
  pwd
)

# DOTENV is the gitignored .env file
DOTENV="$SCRIPTDIR/.env"

# KEYSDIR is the gitignored directory for storing local key files
KEYSDIR="$SCRIPTDIR/keys"
mkdir -p "$KEYSDIR"

# The GCP Project ID
PROJECT_ID=cytoreason

# The dev environment runs the server backend locally (as docker-compose services),
# but retrieves secrets from $K8S_DEPLOYMENTS_CLUSTER
K8S_DEPLOYMENTS_CLUSTER=infra-platform-v2

# The zone of the K8S_DEPLOYMENTS_CLUSTER
K8S_DEPLOYMENTS_CLUSTER_ZONE=europe-west1-b

# A namespace in the cluster in which apps are deployed
APPS_NAMESPACE=apps
DEFAULT_NAMESPACE=default

# set the kubectl context to where the secret is hosted
echo "*** Setting up kubectl context ***"
KUBECONFIGFILE="${KEYSDIR}/kubeconfig"
KUBECLUSTER="infra-platform-v2"
KUBECONFIG="$KUBECONFIGFILE" gcloud container clusters get-credentials "$KUBECLUSTER" --zone "europe-west1-b" --project cytoreason

# get the credentials for the service agent which will be used to authenticate
# store them in the gitignored directory:
GOOGLE_APPLICATION_CREDENTIALS="${KEYSDIR}/credentials.json"
KUBECONFIG="$KUBECONFIGFILE" kubectl -n "$DEFAULT_NAMESPACE" get secret automation-framework-sa-creds -o 'go-template={{index .data "automation-framework.json" }}' | base64 -d > "$GOOGLE_APPLICATION_CREDENTIALS"


rm -f "$DOTENV"
echo "UID=$(id -u)" >>"$DOTENV"
echo "GID=$(id -g)" >>"$DOTENV"
echo "Retrieving secrets from $K8S_DEPLOYMENTS_CLUSTER..."

echo "CYTO_CC_BASE_URL=https://cyto-cc.cytoreason.com" >>"$DOTENV"
echo "CYTO_CC_API_PATH=/api/v1" >>"$DOTENV"
echo "ARTIFACTS_DIR=/ARTIFACTS" >>"$DOTENV"
echo "COMM_DIR=/COMMUNICATION" >>"$DOTENV"


echo "CLIENT_ID_M2M_PUBLIC=18O0q92Yve0Hy74gypPvtcEmuP7Tv8MM" >>"$DOTENV"
echo "#CLIENT_SECRET_M2M_PUBLIC is the Auth0 M2M-public Machine-to-Machine App Client Secret" >>"$DOTENV"
CLIENT_SECRET_M2M_PUBLIC=$(KUBECONFIG="$KUBECONFIGFILE" kubectl -n "$DEFAULT_NAMESPACE" get secrets m2m-secrets -o 'go-template={{index .data "CLIENT_SECRET_M2M_ALL_SCOPES"}}' | base64 -d)
echo "CLIENT_SECRET_M2M_PUBLIC=$CLIENT_SECRET_M2M_PUBLIC" >>"$DOTENV"
echo "CLIENT_ID_M2M_P01_SCOPE=3mVWmGlTEH9HKu0agRUyh4rB1CH30Xwj" >>"$DOTENV"
CLIENT_SECRET_M2M_P01_SCOPE=$(KUBECONFIG="$KUBECONFIGFILE" kubectl -n $APPS_NAMESPACE get secrets storage-secrets -o 'go-template={{index .data "CLIENT_SECRET_p01"}}' | base64 -d)
echo "#CLIENT_SECRET_M2M_P01_SCOPE is the Auth0 M2M-customer-p01 Machine-to-Machine App Client Secret" >>"$DOTENV"
echo "CLIENT_SECRET_M2M_P01_SCOPE=$CLIENT_SECRET_M2M_P01_SCOPE" >>"$DOTENV"
echo "CLIENT_ID_M2M_P13_SCOPE=MwpME8GiqQS98BwbKcp4BumU5peHyvcZ" >>"$DOTENV"
CLIENT_SECRET_M2M_P13_SCOPE=$(KUBECONFIG="$KUBECONFIGFILE" kubectl -n $APPS_NAMESPACE get secrets storage-secrets -o 'go-template={{index .data "CLIENT_SECRET_p13"}}' | base64 -d)
echo "CLIENT_SECRET_M2M_P13_SCOPE=$CLIENT_SECRET_M2M_P13_SCOPE" >>"$DOTENV"

#if [[ "$1" == "p01" ]]; then
#  echo "CLIENT_ID=3mVWmGlTEH9HKu0agRUyh4rB1CH30Xwj" >>"$DOTENV"
#  echo "CLIENT_SECRET=$CLIENT_SECRET_M2M_P01_SCOPE" >>"$DOTENV"
#elif [[ "$1" == "False" ]]; then
#  echo "CLIENT_ID=18O0q92Yve0Hy74gypPvtcEmuP7Tv8MM" >>"$DOTENV"
#  echo "CLIENT_SECRET=$CLIENT_SECRET_M2M_PUBLIC" >>"$DOTENV"
#else
#  # Handle the case when $1 is neither "True" nor "false"
#  echo "CLIENT_ID=MwpME8GiqQS98BwbKcp4BumU5peHyvcZ" >> "$DOTENV"
#  echo "CLIENT_SECRET=$CLIENT_SECRET_M2M_P13_SCOPE" >> "$DOTENV"
#fi

AUTH0_PXX_CLIENT_SECRET_UNITTEST1VIEW=$(KUBECONFIG="$KUBECONFIGFILE" kubectl -n "$DEFAULT_NAMESPACE" get secrets dps-data-api-test-secrets -o 'go-template={{index .data "AUTH0_PXX_CLIENT_SECRET_UNITTEST1VIEW"}}' | base64 -d)
 if [[ "$1" == "R" ]]; then
    echo "CLIENT_ID=jZlg9JCACK3LI0i3sAnYM7MBhOrC8w1f" >>"$DOTENV"
    echo "CLIENT_SECRET=$AUTH0_PXX_CLIENT_SECRET_UNITTEST1VIEW" >>"$DOTENV"
else
    echo "CLIENT_ID=jZlg9JCACK3LI0i3sAnYM7MBhOrC8w1f" >>"$DOTENV"
    echo "CLIENT_SECRET=$AUTH0_PXX_CLIENT_SECRET_UNITTEST1VIEW" >>"$DOTENV"
 fi


#pxx credentials
echo "AUTH0_PXX_CLIENT_ID_UNITTEST1ROLE=jZlg9JCACK3LI0i3sAnYM7MBhOrC8w1f" >>"$DOTENV"
AUTH0_PXX_CLIENT_SECRET_UNITTEST1VIEW=$(KUBECONFIG="$KUBECONFIGFILE" kubectl -n "$DEFAULT_NAMESPACE" get secrets dps-data-api-test-secrets -o 'go-template={{index .data "AUTH0_PXX_CLIENT_SECRET_UNITTEST1VIEW"}}' | base64 -d)
echo "AUTH0_PXX_CLIENT_SECRET_UNITTEST1ROLE=$AUTH0_PXX_CLIENT_SECRET_UNITTEST1VIEW" >>"$DOTENV"
echo "AUTH0_PXX_DOMAIN=cytoreason-pxx.us.auth0.com" >>"$DOTENV"
echo "PXX_ROLE=biologist" >>"$DOTENV"

#pyy credentials
echo "AUTH0_PYY_CLIENT_ID_UNITTEST1ROLE=LgpR6QQnk15S4dSeQmPVhiyDVHRiQKnp" >>"$DOTENV"
CLIENT_SECRET_UNITTEST1ROLE=$(KUBECONFIG="$KUBECONFIGFILE" kubectl -n "$DEFAULT_NAMESPACE" get secrets dps-data-api-test-secrets -o 'go-template={{index .data "AUTH0_PYY_CLIENT_SECRET_UNITTEST1ROLE"}}' | base64 -d)
echo "AUTH0_PYY_CLIENT_SECRET_UNITTEST1ROLE=$CLIENT_SECRET_UNITTEST1ROLE" >>"$DOTENV"
echo "AUTH0_PYY_DOMAIN=cytoreason-pyy.eu.auth0.com" >>"$DOTENV"
echo "PYY_ROLE=automation-biologist" >>"$DOTENV"

#cps admin credentials
echo "AUTH0_CLIENT_ID_M2M_CPS_API=UzMf5nd2hySFm3N5YDxNgqKupcbqFCwM" >>"$DOTENV"
CLIENT_SECRET_M2M_CPS_API=$(KUBECONFIG="$KUBECONFIGFILE" kubectl -n "$DEFAULT_NAMESPACE" get secrets dps-data-api-test-secrets -o 'go-template={{index .data "CLIENT_SECRET_M2M_CPS_API"}}' | base64 -d)
echo "AUTH0_CLIENT_SECRET_M2M_CPS_API=$CLIENT_SECRET_M2M_CPS_API" >>"$DOTENV"

CLIENT_SECRET_M2M_PUBLIC_SCOPE=$(KUBECONFIG="$KUBECONFIGFILE" kubectl -n "$DEFAULT_NAMESPACE" get secrets m2m-secrets -o 'go-template={{index .data "CLIENT_SECRET_M2M_ALL_SCOPES"}}' | base64 -d)
echo "#CLIENT_SECRET_M2M_PUBLIC_SCOPE is the Auth0 M2M-public Machine-to-Machine App Client Secret" >>"$DOTENV"
echo "CLIENT_SECRET_M2M_PUBLIC_SCOPE=$CLIENT_SECRET_M2M_PUBLIC_SCOPE" >>"$DOTENV"
echo "CLIENT_ID_M2M_PUBLIC_SCOPE=18O0q92Yve0Hy74gypPvtcEmuP7Tv8MM" >>"$DOTENV"

echo "CLIENT=Machine" >>"$DOTENV"

echo "GOOGLE_APPLICATION_CREDENTIALS=${GOOGLE_APPLICATION_CREDENTIALS}" >> "$DOTENV"

export PIP_INDEX_URL=https://europe-west1-python.pkg.dev/cytoreason/cytoreason-python-all/simple/
echo "#PIP_INDEX_URL is the url for our python package index" >> "$DOTENV"
echo "PIP_INDEX_URL=$PIP_INDEX_URL" >> "$DOTENV"