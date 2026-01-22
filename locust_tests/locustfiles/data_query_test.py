"""
Data Query Test for CytoReason Platform.

Focuses on heavy data operations - large queries, complex filters.
Tests database and backend performance under data-intensive load.
"""
import random

from locust import HttpUser, between, task

from locust_tests.locustfiles.base import BaseTaskSet
from locust_tests.utils.logger import get_logger

__all__ = ["DataQueryTaskSet", "DataQueryUser"]

logger = get_logger("DataQuery")


class DataQueryTaskSet(BaseTaskSet):
    """
    Data-intensive query testing.
    
    Focuses on endpoints that return large datasets or perform
    complex database operations.
    """

    def on_start(self) -> None:
        """Initialize with multiple disease contexts for variety."""
        super().on_start()
        
        self.diseases = self.config.diseases
        self._rotate_disease()
        
        logger.info(f"Data Query user started")

    def _rotate_disease(self) -> None:
        """Switch to a different disease for query variety."""
        if self.diseases:
            self.disease_config = random.choice(self.diseases)
            self.disease = self.disease_config.disease
            self.context_ids = self.disease_config.context_ids
        else:
            self.disease = "celiac"
            self.context_ids = []

    @task(3)
    def query_gene_data_full(self) -> None:
        """Full gene reference dataset - large response."""
        api_url = self.config.api_platform_url
        payload = self.make_payload()
        
        with self.client.post(
            f"{api_url}/query/fetch?resourceType=gene&responseType=parquet",
            name="Data: Gene Full",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Gene Full")
        
        self.medium_pause()

    @task(3)
    def query_gene_expression_multi_context(self) -> None:
        """Gene expression across multiple contexts."""
        api_url = self.config.api_platform_url
        
        # Use all available context IDs for heavier query
        payload = self.make_payload(
            filters={
                "context_id": self.context_ids,
                "disease": self.disease,
            }
        )
        
        with self.client.post(
            f"{api_url}/query/fetch?resourceType=gene_expression_differences&responseType=parquet",
            name="Data: Gene Expr Multi",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Gene Expr Multi")
        
        self.long_pause()

    @task(3)
    def query_gene_expression_meta(self) -> None:
        """Gene expression metadata - medium dataset."""
        api_url = self.config.api_platform_url
        context_id = random.choice(self.context_ids) if self.context_ids else ""
        
        payload = self.make_payload(
            filters={
                "context_id": [context_id],
                "disease": self.disease,
            }
        )
        
        with self.client.post(
            f"{api_url}/query/fetch?resourceType=gene_expression_differences_meta&responseType=parquet",
            name="Data: Gene Expr Meta",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Gene Expr Meta")
        
        self.medium_pause()

    @task(2)
    def query_cell_abundance_full(self) -> None:
        """Cell abundance across all contexts."""
        api_url = self.config.api_platform_url
        
        payload = self.make_payload(
            filters={
                "context_id": self.context_ids,
                "disease": self.disease,
            }
        )
        
        with self.client.post(
            f"{api_url}/query/fetch?resourceType=cell_abundance_differences&responseType=parquet",
            name="Data: Cell Abundance Full",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Cell Abundance Full")
        
        self.long_pause()

    @task(2)
    def query_cell_abundance_meta(self) -> None:
        """Cell abundance metadata."""
        api_url = self.config.api_platform_url
        
        payload = self.make_payload(
            filters={
                "context_id": self.context_ids,
                "disease": self.disease,
            }
        )
        
        with self.client.post(
            f"{api_url}/query/fetch?resourceType=cell_abundance_differences_meta&responseType=parquet",
            name="Data: Cell Abundance Meta",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Cell Abundance Meta")
        
        self.medium_pause()

    @task(2)
    def query_geneset_grouped_full(self) -> None:
        """Full geneset grouped data."""
        api_url = self.config.api_platform_url
        
        payload = self.make_payload(
            output_fields=["geneset_id:::geneset_name", "collection:::collection_name"]
        )
        
        with self.client.post(
            f"{api_url}/query/fetch?resourceType=geneset_grouped&responseType=parquet",
            name="Data: Geneset Grouped",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Geneset Grouped")
        
        self.medium_pause()

    @task(2)
    def query_geneset_regulation(self) -> None:
        """Geneset regulation - complex query."""
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

    @task(1)
    def query_meta_contexts_map(self) -> None:
        """Meta contexts datasets map."""
        api_url = self.config.api_platform_url
        
        payload = self.make_payload(
            filters={
                "disease": self.disease,
                "relationship": "integrates",
            }
        )
        
        with self.client.post(
            f"{api_url}/query/fetch?resourceType=meta_contexts_datasets_map&responseType=parquet",
            name="Data: Meta Contexts Map",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Meta Contexts Map")
        
        self.medium_pause()

    @task(1)
    def rotate_disease_context(self) -> None:
        """Periodically switch disease for query variety."""
        self._rotate_disease()
        logger.debug(f"Rotated to disease: {self.disease}")


class DataQueryUser(HttpUser):
    """User for data-intensive query testing."""
    
    tasks = [DataQueryTaskSet]
    wait_time = between(2, 5)  # Longer waits for heavy queries
    host = "https://apps.private.cytoreason.com"

    def on_start(self) -> None:
        logger.info(f"Data Query User {id(self)} started")

    def on_stop(self) -> None:
        logger.info(f"Data Query User {id(self)} stopped")
