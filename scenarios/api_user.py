"""
High-throughput API stress user scenario for CytoReason Platform.

Generates the bulk of the load (90%) using lightweight HTTP requests
to stress the backend without the overhead of browser instances.

API Base URL: https://api.platform.private.cytoreason.com/v1.0/customer/pyy/e2/platform
"""

import logging
import random
from typing import Optional

from locust import HttpUser, task, constant, between

from common.config import get_config
from common.auth_util import AuthUtil

logger = logging.getLogger(__name__)


class BackendStresser(HttpUser):
    """
    Pure API user for high-throughput CytoReason backend stress testing.
    
    This user class generates lightweight HTTP requests to stress
    the CytoReason Platform API. It should be spawned 50x more often than
    browser users to generate the bulk of the load while keeping
    resource usage low.
    
    Discovered API Endpoints:
    - /admin/tenant (GET)
    - /project/fetch/catalog (POST)
    - /query/fetch?resourceType=question_index (POST)
    - /query/fetch?resourceType=gene (POST)
    - /query/fetch?resourceType=cell_view (POST)
    - /query/fetch?resourceType=gene_expression_differences (POST)
    - /query/fetch?resourceType=meta_contexts_datasets_map (POST)
    
    Attributes:
        weight: User spawn weight (50x browser users as per plan)
        wait_time: Constant 1 second between requests
    """
    
    # Spawns 50x more often than UIUser (resource-efficient load generation)
    weight = 50
    wait_time = constant(1)
    
    # CytoReason API - use absolute URL to avoid host override issues
    host = "https://api.platform.private.cytoreason.com"
    
    # Full API base URL (used for absolute URL requests)
    API_BASE = "https://api.platform.private.cytoreason.com"
    API_PATH = "/v1.0/customer/pyy/e2/platform"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = get_config()
        self.auth = AuthUtil()
        self._authenticated = False
        # Force the client to use our API base URL
        self.client.base_url = self.API_BASE
        self.api_path = self.API_PATH
        self.current_disease = None
    
    def on_start(self) -> None:
        """Called when a user starts. Perform initial authentication."""
        logger.info(f"BackendStresser user {id(self)} starting")
        
        # Use pre-configured token if available
        if self.config.auth_token:
            self.auth.set_token(self.config.auth_token)
            self._authenticated = True
            logger.debug("Using pre-configured auth token")
        
        # Select a random disease for this user's session
        if self.config.diseases:
            self.current_disease = random.choice(self.config.diseases)
            logger.info(f"User testing disease: {self.current_disease['name']}")
    
    def on_stop(self) -> None:
        """Called when a user stops."""
        logger.info(f"BackendStresser user {id(self)} stopping")
    
    @property
    def auth_headers(self) -> dict:
        """Get authentication headers for requests."""
        return self.auth.get_auth_headers()
    
    def make_payload(self, filters: dict = None, output_fields: list = None) -> dict:
        """Create a standard CytoReason API payload."""
        payload = {}
        if filters:
            payload["filters"] = filters
        if output_fields:
            payload["output_fields"] = output_fields
        return payload
    
    @task(2)
    def health_check(self) -> None:
        """
        API Health check endpoint.
        
        Endpoint: GET /
        Returns: {"status": "UP"}
        """
        with self.client.get(
            "/",
            name="API: Health Check",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(10)
    def get_tenant_info(self) -> None:
        """
        Fetch tenant authentication/configuration.
        
        Endpoint: GET /admin/tenant
        This is called on every page load to verify authentication.
        """
        with self.client.get(
            f"{self.api_path}/admin/tenant",
            headers=self.auth_headers,
            name="API: Tenant Auth",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                response.failure("Unauthorized - check auth token")
            else:
                response.failure(f"Unexpected status: {response.status_code}")
    
    @task(8)
    def fetch_project_catalog(self) -> None:
        """
        Fetch project catalog.
        
        Endpoint: POST /project/fetch/catalog
        Called when loading the main dashboard and programs page.
        """
        with self.client.post(
            f"{self.api_path}/project/fetch/catalog",
            json={},
            headers=self.auth_headers,
            name="API: Project Catalog",
            catch_response=True
        ) as response:
            if response.status_code in (200, 201, 403):  # 403 = permission OK for load test
                response.success()
            elif response.status_code == 401:
                response.failure("401 Unauthorized - Set AUTH_TOKEN env var")
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(7)
    def fetch_question_index(self) -> None:
        """
        Fetch question index for disease navigation.
        
        Endpoint: POST /query/fetch?resourceType=question_index
        """
        disease = self.current_disease["name"].lower() if self.current_disease else "ulcerative colitis"
        payload = self.make_payload(filters={"disease": disease})
        
        with self.client.post(
            f"{self.api_path}/query/fetch",
            params={"resourceType": "question_index", "responseType": "parquet"},
            json=payload,
            headers=self.auth_headers,
            name="API: Question Index",
            catch_response=True
        ) as response:
            if response.status_code in (200, 201, 403):
                # 403 = permission denied but server responded (valid for load test)
                response.success()
            elif response.status_code == 401:
                response.failure("401 Unauthorized - Set AUTH_TOKEN env var")
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(6)
    def fetch_gene_data(self) -> None:
        """
        Fetch gene reference data.
        
        Endpoint: POST /query/fetch?resourceType=gene
        """
        with self.client.post(
            f"{self.api_path}/query/fetch",
            params={"resourceType": "gene", "responseType": "parquet"},
            json=self.make_payload(),
            headers=self.auth_headers,
            name="API: Gene Data",
            catch_response=True
        ) as response:
            if response.status_code in (200, 201, 403):  # 403 = permission OK for load test
                response.success()
            elif response.status_code == 401:
                response.failure("Unauthorized")
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(5)
    def fetch_meta_contexts(self) -> None:
        """
        Fetch meta contexts datasets map.
        
        Endpoint: POST /query/fetch?resourceType=meta_contexts_datasets_map
        """
        disease = self.current_disease["name"].lower() if self.current_disease else "ulcerative colitis"
        payload = self.make_payload(
            filters={"disease": disease, "relationship": "integrates"}
        )
        
        with self.client.post(
            f"{self.api_path}/query/fetch",
            params={"resourceType": "meta_contexts_datasets_map", "responseType": "parquet"},
            json=payload,
            headers=self.auth_headers,
            name="API: Meta Contexts",
            catch_response=True
        ) as response:
            if response.status_code in (200, 201, 403):  # 403 = permission OK for load test
                response.success()
            elif response.status_code == 401:
                response.failure("Unauthorized")
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(5)
    def fetch_gene_expression_meta(self) -> None:
        """
        Fetch gene expression differences metadata.
        
        Endpoint: POST /query/fetch?resourceType=gene_expression_differences_meta
        """
        disease = self.current_disease["name"].lower() if self.current_disease else "ulcerative colitis"
        payload = self.make_payload(filters={"disease": disease})
        
        with self.client.post(
            f"{self.api_path}/query/fetch",
            params={"resourceType": "gene_expression_differences_meta", "responseType": "parquet"},
            json=payload,
            headers=self.auth_headers,
            name="API: Gene Expr Meta",
            catch_response=True
        ) as response:
            if response.status_code in (200, 201, 403):  # 403 = permission OK for load test
                response.success()
            elif response.status_code == 401:
                response.failure("Unauthorized")
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(3)
    def fetch_model_diseases(self) -> None:
        """
        Fetch available disease models.
        
        Endpoint: POST /query/fetch?resourceType=model_diseases
        """
        with self.client.post(
            f"{self.api_path}/query/fetch",
            params={"resourceType": "model_diseases", "response_type": "json"},
            json=self.make_payload(),
            headers=self.auth_headers,
            name="API: Model Diseases",
            catch_response=True
        ) as response:
            if response.status_code in (200, 201, 403):  # 403 = permission OK for load test
                response.success()
            elif response.status_code == 401:
                response.failure("Unauthorized")
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(2)
    def fetch_cell_view(self) -> None:
        """
        Fetch cell view data.
        
        Endpoint: POST /query/fetch?resourceType=cell_view
        """
        with self.client.post(
            f"{self.api_path}/query/fetch",
            params={"resourceType": "cell_view", "responseType": "parquet"},
            json=self.make_payload(),
            headers=self.auth_headers,
            name="API: Cell View",
            catch_response=True
        ) as response:
            if response.status_code in (200, 201, 403):  # 403 = permission OK for load test
                response.success()
            elif response.status_code == 401:
                response.failure("Unauthorized")
            else:
                response.failure(f"Status: {response.status_code}")
    
    @task(1)
    def fetch_total_counters(self) -> None:
        """
        Fetch project counters (dashboard stats).
        
        Endpoint: POST /query/fetch?resourceType=total_project_counters
        """
        with self.client.post(
            f"{self.api_path}/query/fetch",
            params={"resourceType": "total_project_counters", "response_type": "json"},
            json=self.make_payload(),
            headers=self.auth_headers,
            name="API: Project Counters",
            catch_response=True
        ) as response:
            if response.status_code in (200, 201, 403):  # 403 = permission OK for load test
                response.success()
            elif response.status_code == 401:
                response.failure("Unauthorized")
            else:
                response.failure(f"Status: {response.status_code}")
