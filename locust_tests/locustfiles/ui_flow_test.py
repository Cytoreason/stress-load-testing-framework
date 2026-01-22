"""
UI User Flow Load Test for CytoReason Platform.

Simulates realistic user journeys through the platform based on
actual API calls captured from HAR file analysis.

Discovered resourceTypes:
- question_index, dataset, gene, cell_signature, cell_view
- gene_expression_differences, gene_expression_differences_meta
- cell_abundance_differences, cell_abundance_differences_meta
- geneset_expression_regulation_differences, geneset_grouped
- meta_contexts_datasets_map, cr_target_disease, entity_activity
- experimental_context, and more...
"""
import random
from typing import Any

from locust import HttpUser, between, task

from locust_tests.locustfiles.base import BaseTaskSet
from locust_tests.utils.config_loader import DiseaseConfig
from locust_tests.utils.logger import get_logger

__all__ = ["UIFlowTaskSet", "UIFlowUser"]

logger = get_logger("UIFlow")


class UIFlowTaskSet(BaseTaskSet):
    """
    Sequential user journey based on real HAR file captures.

    Simulates a complete user session through the CytoReason platform,
    including authentication, data exploration, and disease switching.

    Test Steps (ST-01 to ST-15):
        ST-01: Landing page and tenant authentication
        ST-02: Project catalog fetch
        ST-03: Question index navigation
        ST-04: Gene reference data
        ST-05: Disease Explorer page
        ST-06: Meta contexts datasets map
        ST-07: Gene expression differences metadata
        ST-08: Gene expression differences
        ST-09: Cell abundance differences
        ST-10: Geneset grouped data
        ST-11: Geneset expression regulation
        ST-12: Target-Cell Association page
        ST-13: Cell abundance metadata
        ST-14: Disease switching
        ST-15: Return to landing (journey complete)
    """

    # Current test state
    disease_config: DiseaseConfig
    disease: str
    tissue: str
    context_ids: list[str]

    def on_start(self) -> None:
        """Initialize user session with random disease configuration."""
        super().on_start()

        # Select random disease for this user's journey
        diseases = self.config.diseases
        if not diseases:
            logger.error("No disease configurations available")
            return

        self.disease_config = random.choice(diseases)
        self.disease = self.disease_config.disease
        self.tissue = self.disease_config.tissue
        self.context_ids = self.disease_config.context_ids

        if self.config.bearer_token:
            logger.info(
                f"User {id(self.user)} started - disease: {self.disease}, "
                f"tissue: {self.tissue}"
            )
        else:
            logger.warning(
                f"User {id(self.user)} started UNAUTHENTICATED - "
                "requests may fail with 401"
            )

    # ========== STEP 1: Landing & Tenant ==========
    @task
    def st01_landing_tenant(self) -> None:
        """ST-01: Landing page and tenant info."""
        base_path = self.config.platform_base_path
        api_url = self.config.api_platform_url

        # Landing page
        with self.client.get(
            f"{base_path}/",
            name="ST-01: Landing Page",
            catch_response=True,
        ) as response:
            self.check_response(response, "Landing Page", (200, 302))

        # Tenant authentication check
        with self.client.get(
            f"{api_url}/admin/tenant",
            name="ST-01: Tenant Auth",
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            if self.check_response(response, "Tenant Auth"):
                logger.debug("Authentication verified")

        self.short_pause()

    # ========== STEP 2: Project Catalog ==========
    @task
    def st02_project_catalog(self) -> None:
        """ST-02: Fetch project catalog."""
        api_url = self.config.api_platform_url

        with self.client.post(
            f"{api_url}/project/fetch/catalog",
            name="ST-02: Project Catalog",
            json={},
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Project Catalog")

        self.short_pause()

    # ========== STEP 3: Question Index ==========
    @task
    def st03_question_index(self) -> None:
        """ST-03: Fetch question index for navigation."""
        api_url = self.config.api_platform_url
        payload = self.make_payload(filters={"disease": self.disease})

        with self.client.post(
            f"{api_url}/query/fetch?resourceType=question_index&responseType=parquet",
            name="ST-03: Question Index",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Question Index")

        self.medium_pause()

    # ========== STEP 4: Gene Data ==========
    @task
    def st04_gene_data(self) -> None:
        """ST-04: Fetch gene reference data."""
        api_url = self.config.api_platform_url
        payload = self.make_payload()

        with self.client.post(
            f"{api_url}/query/fetch?resourceType=gene&responseType=parquet",
            name="ST-04: Gene Data",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Gene Data")

        self.medium_pause()

    # ========== STEP 5: Disease Explorer Page ==========
    @task
    def st05_disease_explorer(self) -> None:
        """ST-05: Navigate to Disease Explorer."""
        base_path = self.config.platform_base_path

        with self.client.get(
            f"{base_path}/disease-explorer/differential-expression",
            name="ST-05: Disease Explorer",
            catch_response=True,
        ) as response:
            self.check_response(response, "Disease Explorer", (200, 302))

        self.short_pause()

    # ========== STEP 6: Meta Contexts Datasets Map ==========
    @task
    def st06_meta_contexts(self) -> None:
        """ST-06: Fetch meta contexts datasets map."""
        api_url = self.config.api_platform_url
        payload = self.make_payload(
            filters={
                "disease": self.disease,
                "relationship": "integrates",
            }
        )

        with self.client.post(
            f"{api_url}/query/fetch?resourceType=meta_contexts_datasets_map&responseType=parquet",
            name="ST-06: Meta Contexts",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Meta Contexts")

        self.medium_pause()

    # ========== STEP 7: Gene Expression Differences Meta ==========
    @task
    def st07_gene_expression_meta(self) -> None:
        """ST-07: Fetch gene expression differences metadata."""
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
            name="ST-07: Gene Expr Meta",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Gene Expr Meta")

        self.think_time(1.0, 3.0)

    # ========== STEP 8: Gene Expression Differences ==========
    @task
    def st08_gene_expression(self) -> None:
        """ST-08: Fetch gene expression differences."""
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
            name="ST-08: Gene Expression",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Gene Expression")

        self.long_pause()

    # ========== STEP 9: Cell Abundance Differences ==========
    @task
    def st09_cell_abundance(self) -> None:
        """ST-09: Fetch cell abundance differences."""
        api_url = self.config.api_platform_url
        payload = self.make_payload(
            filters={
                "context_id": self.context_ids,
                "disease": self.disease,
            }
        )

        with self.client.post(
            f"{api_url}/query/fetch?resourceType=cell_abundance_differences&responseType=parquet",
            name="ST-09: Cell Abundance",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Cell Abundance")

        self.long_pause()

    # ========== STEP 10: Geneset Grouped ==========
    @task
    def st10_geneset_grouped(self) -> None:
        """ST-10: Fetch geneset grouped data."""
        api_url = self.config.api_platform_url
        payload = self.make_payload(
            output_fields=["geneset_id:::geneset_name", "collection:::collection_name"]
        )

        with self.client.post(
            f"{api_url}/query/fetch?resourceType=geneset_grouped&responseType=parquet",
            name="ST-10: Geneset Grouped",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Geneset Grouped")

        self.medium_pause()

    # ========== STEP 11: Geneset Expression Regulation ==========
    @task
    def st11_geneset_regulation(self) -> None:
        """ST-11: Fetch geneset expression regulation differences."""
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
            name="ST-11: Geneset Regulation",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Geneset Regulation")

        self.think_time(2.0, 3.0)

    # ========== STEP 12: Target-Cell Association Page ==========
    @task
    def st12_target_cell_page(self) -> None:
        """ST-12: Navigate to Target-Cell Association."""
        base_path = self.config.platform_base_path

        with self.client.get(
            f"{base_path}/disease-explorer/target-cell-association",
            name="ST-12: Target-Cell Page",
            catch_response=True,
        ) as response:
            self.check_response(response, "Target-Cell Page", (200, 302))

        self.short_pause()

    # ========== STEP 13: Cell Abundance Meta ==========
    @task
    def st13_cell_abundance_meta(self) -> None:
        """ST-13: Fetch cell abundance differences metadata."""
        api_url = self.config.api_platform_url
        payload = self.make_payload(
            filters={
                "context_id": self.context_ids,
                "disease": self.disease,
            }
        )

        with self.client.post(
            f"{api_url}/query/fetch?resourceType=cell_abundance_differences_meta&responseType=parquet",
            name="ST-13: Cell Abundance Meta",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            self.check_response(response, "Cell Abundance Meta")

        self.medium_pause()

    # ========== STEP 14: Switch Disease ==========
    @task
    def st14_switch_disease(self) -> None:
        """ST-14: Switch to a different disease."""
        api_url = self.config.api_platform_url

        # Select a different disease
        available = [d for d in self.config.diseases if d.disease != self.disease]
        if not available:
            available = self.config.diseases

        self.disease_config = random.choice(available)
        self.disease = self.disease_config.disease
        self.tissue = self.disease_config.tissue
        self.context_ids = self.disease_config.context_ids

        payload = self.make_payload(filters={"disease": self.disease})

        with self.client.post(
            f"{api_url}/query/fetch?resourceType=question_index&responseType=parquet",
            name="ST-14: Switch Disease",
            json=payload,
            headers=self.auth_headers,
            catch_response=True,
        ) as response:
            if self.check_response(response, "Switch Disease"):
                logger.debug(f"Switched to disease: {self.disease}")

        self.medium_pause()

    # ========== STEP 15: Return to Landing ==========
    @task
    def st15_return_landing(self) -> None:
        """ST-15: Return to landing (complete journey)."""
        base_path = self.config.platform_base_path

        with self.client.get(
            f"{base_path}/",
            name="ST-15: Return Landing",
            catch_response=True,
        ) as response:
            if self.check_response(response, "Return Landing", (200, 302)):
                logger.info(f"User {id(self.user)} completed journey")

        self.short_pause()


class UIFlowUser(HttpUser):
    """
    User class for UI flow load testing.

    Locust spawns instances of this class to simulate concurrent users
    navigating through the platform.

    Attributes:
        tasks: List of task sets to execute
        wait_time: Random wait between task iterations (1-3 seconds)
        host: Default target host
    """

    tasks = [UIFlowTaskSet]
    wait_time = between(1, 3)
    host = "https://apps.private.cytoreason.com"

    def on_start(self) -> None:
        """Called when a new user starts."""
        logger.info(f"UI Flow User {id(self)} started")

    def on_stop(self) -> None:
        """Called when a user stops."""
        logger.info(f"UI Flow User {id(self)} stopped")
