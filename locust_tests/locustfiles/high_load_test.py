"""
High Load Test - 100 Concurrent Users on CytoReason Platform.

Simulates 100 concurrent users performing various actions:
- Browsing disease explorer pages
- Querying gene expression data
- Fetching cell abundance information
- Switching between diseases
- Loading project catalogs

This test focuses on realistic mixed workload patterns.
"""
import random
from typing import Any

from locust import HttpUser, LoadTestShape, TaskSet, between, task

from locust_tests.locustfiles.base import BaseTaskSet
from locust_tests.utils.config_loader import DiseaseConfig
from locust_tests.utils.logger import get_logger

__all__ = ["HighLoadTaskSet", "HighLoadUser", "HighLoadTestShape"]

logger = get_logger("HighLoad")


class HighLoadTaskSet(BaseTaskSet):
    """
    Mixed workload task set for high-load testing.
    
    Simulates realistic user behavior with weighted tasks:
    - Heavy data queries (gene expression, cell abundance)
    - Light browsing (landing pages, navigation)
    - Medium queries (project catalog, question index)
    """
    
    disease_config: DiseaseConfig
    disease: str
    tissue: str
    context_ids: list[str]
    
    def on_start(self) -> None:
        """Initialize user session."""
        super().on_start()
        
        # Select random disease configuration
        diseases = self.config.diseases
        if diseases:
            self.disease_config = random.choice(diseases)
            self.disease = self.disease_config.disease
            self.tissue = self.disease_config.tissue
            self.context_ids = self.disease_config.context_ids
        else:
            self.disease = "systemic sclerosis"
            self.tissue = "skin"
            self.context_ids = []
        
        logger.info(f"User {id(self.user)} started - disease: {self.disease}")
    
    # ==================== LIGHT TASKS (High frequency) ====================
    
    @task(10)
    def browse_landing(self) -> None:
        """Browse landing page - lightweight request."""
        base_path = self.config.platform_base_path
        
        with self.client.get(
            f"{base_path}/",
            name="Browse: Landing Page",
            catch_response=True,
        ) as response:
            self.check_response(response, "Landing", (200, 302))
        
        self.short_pause()
    
    @task(8)
    def browse_disease_explorer(self) -> None:
        """Navigate to disease explorer page."""
        base_path = self.config.platform_base_path
        
        pages = [
            "/disease-explorer/differential-expression",
            "/disease-explorer/target-cell-association",
            "/disease-explorer/geneset-regulation",
        ]
        page = random.choice(pages)
        
        with self.client.get(
            f"{base_path}{page}",
            name=f"Browse: Disease Explorer",
            catch_response=True,
        ) as response:
            self.check_response(response, "Disease Explorer", (200, 302))
        
        self.short_pause()
    
    @task(6)
    def check_tenant_auth(self) -> None:
        """Verify authentication status."""
        api_url = self.config.api_platform_url
        
        with self.client.get(
            f"{api_url}/admin/tenant",
            name="Auth: Tenant Check",
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Tenant Auth")
        
        self.short_pause()
    
    # ==================== MEDIUM TASKS (Moderate frequency) ====================
    
    @task(5)
    def fetch_project_catalog(self) -> None:
        """Fetch project catalog."""
        api_url = self.config.api_platform_url
        
        with self.client.post(
            f"{api_url}/project/fetch/catalog",
            name="Query: Project Catalog",
            json={},
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Project Catalog")
        
        self.medium_pause()
    
    @task(5)
    def fetch_question_index(self) -> None:
        """Fetch question index for current disease."""
        api_url = self.config.api_platform_url
        payload = self.make_payload(filters={"disease": self.disease})
        
        with self.client.post(
            f"{api_url}/query/fetch?resourceType=question_index&responseType=parquet",
            name="Query: Question Index",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Question Index")
        
        self.medium_pause()
    
    @task(4)
    def fetch_meta_contexts(self) -> None:
        """Fetch meta contexts datasets map."""
        api_url = self.config.api_platform_url
        payload = self.make_payload(
            filters={
                "disease": self.disease,
                "relationship": "integrates",
            }
        )
        
        with self.client.post(
            f"{api_url}/query/fetch?resourceType=meta_contexts_datasets_map&responseType=parquet",
            name="Query: Meta Contexts",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Meta Contexts")
        
        self.medium_pause()
    
    @task(4)
    def fetch_geneset_grouped(self) -> None:
        """Fetch geneset grouped data."""
        api_url = self.config.api_platform_url
        payload = self.make_payload(
            output_fields=["geneset_id:::geneset_name", "collection:::collection_name"]
        )
        
        with self.client.post(
            f"{api_url}/query/fetch?resourceType=geneset_grouped&responseType=parquet",
            name="Query: Geneset Grouped",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Geneset Grouped")
        
        self.medium_pause()
    
    # ==================== HEAVY TASKS (Lower frequency) ====================
    
    @task(3)
    def fetch_gene_data(self) -> None:
        """Fetch gene reference data - heavy payload."""
        api_url = self.config.api_platform_url
        payload = self.make_payload()
        
        with self.client.post(
            f"{api_url}/query/fetch?resourceType=gene&responseType=parquet",
            name="Data: Gene Reference",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Gene Data")
        
        self.long_pause()
    
    @task(2)
    def fetch_gene_expression(self) -> None:
        """Fetch gene expression differences - heavy query."""
        api_url = self.config.api_platform_url
        context_id = random.choice(self.context_ids) if self.context_ids else ""
        
        payload = self.make_payload(
            filters={
                "context_id": [context_id],
                "disease": self.disease,
            }
        )
        
        with self.client.post(
            f"{api_url}/query/fetch?resourceType=gene_expression_differences&responseType=parquet",
            name="Data: Gene Expression",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Gene Expression")
        
        self.long_pause()
    
    @task(2)
    def fetch_cell_abundance(self) -> None:
        """Fetch cell abundance differences - heavy query."""
        api_url = self.config.api_platform_url
        payload = self.make_payload(
            filters={
                "context_id": self.context_ids,
                "disease": self.disease,
            }
        )
        
        with self.client.post(
            f"{api_url}/query/fetch?resourceType=cell_abundance_differences&responseType=parquet",
            name="Data: Cell Abundance",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Cell Abundance")
        
        self.long_pause()
    
    @task(2)
    def fetch_geneset_regulation(self) -> None:
        """Fetch geneset regulation - heavy query."""
        api_url = self.config.api_platform_url
        context_id = random.choice(self.context_ids) if self.context_ids else ""
        
        payload = self.make_payload(
            filters={
                "context_id": [context_id],
                "disease": self.disease,
                "collection": "cr-target",
            }
        )
        
        with self.client.post(
            f"{api_url}/query/fetch?resourceType=geneset_expression_regulation_differences&responseType=parquet",
            name="Data: Geneset Regulation",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Geneset Regulation")
        
        self.long_pause()
    
    # ==================== SPECIAL TASKS ====================
    
    @task(1)
    def switch_disease(self) -> None:
        """Switch to a different disease context."""
        # Select a different disease
        available = [d for d in self.config.diseases if d.disease != self.disease]
        if not available:
            available = self.config.diseases
        
        if available:
            self.disease_config = random.choice(available)
            self.disease = self.disease_config.disease
            self.tissue = self.disease_config.tissue
            self.context_ids = self.disease_config.context_ids
            
            logger.debug(f"User {id(self.user)} switched to: {self.disease}")
        
        # Fetch new question index for switched disease
        api_url = self.config.api_platform_url
        payload = self.make_payload(filters={"disease": self.disease})
        
        with self.client.post(
            f"{api_url}/query/fetch?resourceType=question_index&responseType=parquet",
            name="Action: Switch Disease",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Switch Disease")
        
        self.medium_pause()


class HighLoadUser(HttpUser):
    """
    User class for high-load testing with 100 concurrent users.
    
    Attributes:
        tasks: Mixed workload task set
        wait_time: Random wait between 0.5-2 seconds (faster pacing)
        host: Target CytoReason platform
    """
    
    tasks = [HighLoadTaskSet]
    wait_time = between(0.5, 2)  # Faster pacing for high load
    host = "https://apps.private.cytoreason.com"
    
    def on_start(self) -> None:
        """Called when user starts."""
        logger.info(f"High Load User {id(self)} started")
    
    def on_stop(self) -> None:
        """Called when user stops."""
        logger.info(f"High Load User {id(self)} stopped")


class HighLoadTestShape(LoadTestShape):
    """
    Load shape for 100 concurrent users test.
    
    Ramp-up pattern:
    1. 0-2 min: Warm up to 20 users (gradual start)
    2. 2-5 min: Ramp to 50 users
    3. 5-8 min: Ramp to 100 users (peak load)
    4. 8-15 min: Hold at 100 users (sustained load)
    5. 15-18 min: Ramp down to 50 users
    6. 18-20 min: Ramp down to 0 (cooldown)
    
    Total duration: 20 minutes
    """
    
    stages = [
        # (duration_seconds, users, spawn_rate)
        {"duration": 120, "users": 20, "spawn_rate": 2.0},    # Warm up
        {"duration": 300, "users": 50, "spawn_rate": 2.0},    # Ramp to 50
        {"duration": 480, "users": 100, "spawn_rate": 3.0},   # Ramp to 100
        {"duration": 900, "users": 100, "spawn_rate": 3.0},   # Hold at 100
        {"duration": 1080, "users": 50, "spawn_rate": 2.0},   # Ramp down to 50
        {"duration": 1200, "users": 0, "spawn_rate": 2.0},    # Cooldown
    ]
    
    def tick(self) -> tuple[int, float] | None:
        """Return (user_count, spawn_rate) for current time."""
        run_time = self.get_run_time()
        
        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])
        
        # Test complete
        return None
