"""
API Stress Test for CytoReason Platform.

Direct API endpoint testing without sequential flow constraints.
Tests individual endpoints under concurrent load.
"""
import random
from typing import Any

from locust import HttpUser, between, task

from locust_tests.locustfiles.base import BaseTaskSet
from locust_tests.utils.logger import get_logger

__all__ = ["APIStressTaskSet", "APIStressUser"]

logger = get_logger("APIStress")


class APIStressTaskSet(BaseTaskSet):
    """
    Concurrent API stress testing.
    
    Unlike UIFlowTaskSet, this executes tasks randomly based on weight,
    simulating multiple users hitting different endpoints simultaneously.
    """

    # Test data
    genes: list[str] = ["BRCA1", "TP53", "EGFR", "KRAS", "MYC", "PTEN"]
    collections: list[str] = ["cr-target", "hallmark", "kegg"]

    def on_start(self) -> None:
        """Initialize user session."""
        super().on_start()
        
        diseases = self.config.diseases
        self.disease_config = random.choice(diseases) if diseases else None
        self.disease = self.disease_config.disease if self.disease_config else "celiac"
        self.context_ids = self.disease_config.context_ids if self.disease_config else []
        
        logger.info(f"Stress user started - disease: {self.disease}")

    @task(10)
    def fetch_tenant(self) -> None:
        """High frequency: Tenant auth check."""
        api_url = self.config.api_platform_url
        
        with self.client.get(
            f"{api_url}/admin/tenant",
            name="API: Tenant Auth",
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Tenant Auth")

    @task(8)
    def fetch_project_catalog(self) -> None:
        """High frequency: Project catalog."""
        api_url = self.config.api_platform_url
        
        with self.client.post(
            f"{api_url}/project/fetch/catalog",
            name="API: Project Catalog",
            json={},
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Project Catalog")

    @task(5)
    def fetch_question_index(self) -> None:
        """Medium frequency: Question index."""
        api_url = self.config.api_platform_url
        payload = self.make_payload(filters={"disease": self.disease})
        
        with self.client.post(
            f"{api_url}/query/fetch?resourceType=question_index&responseType=parquet",
            name="API: Question Index",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Question Index")

    @task(3)
    def fetch_gene_data(self) -> None:
        """Medium frequency: Gene reference data."""
        api_url = self.config.api_platform_url
        payload = self.make_payload()
        
        with self.client.post(
            f"{api_url}/query/fetch?resourceType=gene&responseType=parquet",
            name="API: Gene Data",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Gene Data")

    @task(3)
    def fetch_meta_contexts(self) -> None:
        """Medium frequency: Meta contexts map."""
        api_url = self.config.api_platform_url
        payload = self.make_payload(
            filters={"disease": self.disease, "relationship": "integrates"}
        )
        
        with self.client.post(
            f"{api_url}/query/fetch?resourceType=meta_contexts_datasets_map&responseType=parquet",
            name="API: Meta Contexts",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Meta Contexts")

    @task(2)
    def fetch_gene_expression(self) -> None:
        """Lower frequency: Heavy gene expression query."""
        api_url = self.config.api_platform_url
        context_id = random.choice(self.context_ids) if self.context_ids else ""
        
        payload = self.make_payload(
            filters={"context_id": [context_id], "disease": self.disease}
        )
        
        with self.client.post(
            f"{api_url}/query/fetch?resourceType=gene_expression_differences&responseType=parquet",
            name="API: Gene Expression",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Gene Expression")

    @task(2)
    def fetch_cell_abundance(self) -> None:
        """Lower frequency: Cell abundance data."""
        api_url = self.config.api_platform_url
        
        payload = self.make_payload(
            filters={"context_id": self.context_ids, "disease": self.disease}
        )
        
        with self.client.post(
            f"{api_url}/query/fetch?resourceType=cell_abundance_differences&responseType=parquet",
            name="API: Cell Abundance",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Cell Abundance")

    @task(2)
    def fetch_geneset_grouped(self) -> None:
        """Lower frequency: Geneset grouped."""
        api_url = self.config.api_platform_url
        
        payload = self.make_payload(
            output_fields=["geneset_id:::geneset_name", "collection:::collection_name"]
        )
        
        with self.client.post(
            f"{api_url}/query/fetch?resourceType=geneset_grouped&responseType=parquet",
            name="API: Geneset Grouped",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Geneset Grouped")

    @task(1)
    def fetch_geneset_regulation(self) -> None:
        """Low frequency: Heavy geneset regulation query."""
        api_url = self.config.api_platform_url
        context_id = random.choice(self.context_ids) if self.context_ids else ""
        collection = random.choice(self.collections)
        
        payload = self.make_payload(
            filters={
                "context_id": [context_id],
                "disease": self.disease,
                "collection": collection,
            }
        )
        
        with self.client.post(
            f"{api_url}/query/fetch?resourceType=geneset_expression_regulation_differences&responseType=parquet",
            name="API: Geneset Regulation",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Geneset Regulation")


class APIStressUser(HttpUser):
    """User for API stress testing with random endpoint access."""
    
    tasks = [APIStressTaskSet]
    wait_time = between(0.5, 2)
    host = "https://apps.private.cytoreason.com"

    def on_start(self) -> None:
        logger.info(f"API Stress User {id(self)} started")

    def on_stop(self) -> None:
        logger.info(f"API Stress User {id(self)} stopped")
