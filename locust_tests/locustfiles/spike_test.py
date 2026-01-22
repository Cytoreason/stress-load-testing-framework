"""
Spike Test for CytoReason Platform.

Tests system resilience under sudden load increases.
Simulates traffic spikes to identify breaking points.
"""
import random

from locust import HttpUser, between, task, LoadTestShape

from locust_tests.locustfiles.base import BaseTaskSet
from locust_tests.utils.logger import get_logger

__all__ = ["SpikeTaskSet", "SpikeUser", "SpikeTestShape"]

logger = get_logger("Spike")


class SpikeTaskSet(BaseTaskSet):
    """
    Fast-paced task set for spike testing.
    
    Minimal think time, high request frequency to maximize load.
    """

    def on_start(self) -> None:
        """Initialize user session."""
        super().on_start()
        
        diseases = self.config.diseases
        self.disease_config = random.choice(diseases) if diseases else None
        self.disease = self.disease_config.disease if self.disease_config else "celiac"
        self.context_ids = self.disease_config.context_ids if self.disease_config else []

    @task(5)
    def quick_auth_check(self) -> None:
        """Fast auth verification."""
        api_url = self.config.api_platform_url
        
        with self.client.get(
            f"{api_url}/admin/tenant",
            name="Spike: Auth",
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Auth")

    @task(4)
    def quick_catalog(self) -> None:
        """Fast catalog fetch."""
        api_url = self.config.api_platform_url
        
        with self.client.post(
            f"{api_url}/project/fetch/catalog",
            name="Spike: Catalog",
            json={},
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Catalog")

    @task(3)
    def quick_question_index(self) -> None:
        """Fast question index."""
        api_url = self.config.api_platform_url
        payload = self.make_payload(filters={"disease": self.disease})
        
        with self.client.post(
            f"{api_url}/query/fetch?resourceType=question_index&responseType=parquet",
            name="Spike: Question Index",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Question Index")

    @task(2)
    def quick_meta_contexts(self) -> None:
        """Fast meta contexts."""
        api_url = self.config.api_platform_url
        payload = self.make_payload(
            filters={"disease": self.disease, "relationship": "integrates"}
        )
        
        with self.client.post(
            f"{api_url}/query/fetch?resourceType=meta_contexts_datasets_map&responseType=parquet",
            name="Spike: Meta Contexts",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Meta Contexts")

    @task(1)
    def quick_gene_expression(self) -> None:
        """Fast gene expression query."""
        api_url = self.config.api_platform_url
        context_id = random.choice(self.context_ids) if self.context_ids else ""
        
        payload = self.make_payload(
            filters={"context_id": [context_id], "disease": self.disease}
        )
        
        with self.client.post(
            f"{api_url}/query/fetch?resourceType=gene_expression_differences&responseType=parquet",
            name="Spike: Gene Expression",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Gene Expression")


class SpikeUser(HttpUser):
    """User for spike testing with minimal wait time."""
    
    tasks = [SpikeTaskSet]
    wait_time = between(0.1, 0.5)  # Very short wait for spike effect
    host = "https://apps.private.cytoreason.com"

    def on_start(self) -> None:
        logger.info(f"Spike User {id(self)} started")

    def on_stop(self) -> None:
        logger.info(f"Spike User {id(self)} stopped")


class SpikeTestShape(LoadTestShape):
    """
    Spike load pattern - sudden traffic bursts.
    
    Pattern:
        0-1 min:  5 users (baseline)
        1-2 min:  50 users (SPIKE!)
        2-3 min:  5 users (recovery)
        3-4 min:  75 users (BIGGER SPIKE!)
        4-5 min:  5 users (recovery)
        5-6 min:  100 users (MAX SPIKE!)
        6-7 min:  5 users (cooldown)
        
    Total: 7 minutes
    """
    
    stages = [
        {"duration": 60, "users": 5, "spawn_rate": 5},      # Baseline
        {"duration": 120, "users": 50, "spawn_rate": 50},   # Spike 1
        {"duration": 180, "users": 5, "spawn_rate": 10},    # Recovery
        {"duration": 240, "users": 75, "spawn_rate": 75},   # Spike 2
        {"duration": 300, "users": 5, "spawn_rate": 10},    # Recovery
        {"duration": 360, "users": 100, "spawn_rate": 100}, # Max spike
        {"duration": 420, "users": 5, "spawn_rate": 10},    # Cooldown
    ]

    def tick(self):
        """Return current user count based on time."""
        run_time = self.get_run_time()
        
        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])
        
        return None
