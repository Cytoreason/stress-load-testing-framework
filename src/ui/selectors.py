"""
Validated UI selectors for the CytoReason platform.

VALIDATION NOTES
----------------
All selectors below were derived from real platform codebase inspection
and interaction with the live staging environment:

  Target: https://apps.private.cytoreason.com/platform/customers/pyy/

SELECTOR STRATEGY
-----------------
Priority order (most to least stable):
  1. ARIA role + accessible name  → get_by_role(role, name=...)
  2. Label text                   → get_by_label(label)
  3. Placeholder text             → get_by_placeholder(text)
  4. Visible text content         → get_by_text(text)
  5. Test ID attribute            → get_by_test_id(id)  [use if available]
  6. CSS class / ID               [last resort – avoid]

Re-validation: Run `pytest -m selector` to verify all selectors are still
present before any load or stress run.
"""
from __future__ import annotations

from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Auth0 Login page
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class _LoginSelectors:
    # Auth0 universal login form labels (validated on staging)
    username_input_label: str = "Email address *"
    password_input_label: str = "Password *"
    continue_button_name: str = "Continue"


# ---------------------------------------------------------------------------
# Application "ready" signal – element visible only after successful login
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class _AppReadySelectors:
    # Navigation link that exists exclusively in an authenticated session
    # Validated: first visible nav link on Programs landing page
    landing_unique_role: str = "link"
    landing_unique_name: str = "Programs"


# ---------------------------------------------------------------------------
# Programs / Projects page  (/programs)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class _ProgramsSelectors:
    # Search textbox accessible name (role=textbox, name=...)
    search_accessible_name: str = "Search program, project or model..."

    # Filter toggle buttons (role=button, name=...)
    my_projects_button: str = "My Projects"
    all_projects_button: str = "All Projects"


# ---------------------------------------------------------------------------
# Inventory page  (accessible via Disease Explorer side nav)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class _InventorySelectors:
    # Side-nav link that navigates to the Inventory view
    inventory_link_name: str = "Inventory"

    # Disease Biology accordion / category button
    disease_biology_button: str = "Disease Biology"

    # Individual inventory items (role=link, name=exact text)
    item_target_expression: str = "1 . Target Expression in Disease"
    item_target_regulation: str = "2 . Target Regulation in Disease"
    item_cell_abundance: str = "3 . Differential Cell Abundance in Disease"
    item_disease_severity: str = "7 . Association with disease severity"
    item_soc_treatment: str = "8 . Standard of care (SOC) treatment effect spaces"


# ---------------------------------------------------------------------------
# Disease Explorer / DX page  (/disease-explorer/differential-expression)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class _DxSelectors:
    # URL path suffix for the Differential Expression DX view
    de_path: str = "/disease-explorer/differential-expression"

    # Disease model selector comboboxes (role=combobox, name=partial match)
    # Validated names from the live ASTH model page
    asth_model_combobox: str = "ASTH Disease Model Asthma"

    # "Disease Models" menu button in side-nav
    disease_models_button: str = "Disease Models"

    # Analysis type radio buttons
    radio_white_space: str = "White Space"
    radio_target_signature: str = "Target Signature"

    # Filter comboboxes on the ASTH DX view (validated names)
    combobox_bronchus: str = "bronchus"
    combobox_disease_vs_control: str = "disease vs control"
    combobox_fluticasone: str = "Fluticasone"
    combobox_week1_500ug: str = "Week 1, 500 μg"

    # Additional disease model nav links (regex-friendly exact prefixes)
    copd_model_link_prefix: str = "COPD"
    uc_model_link_prefix: str = "UC"


# ---------------------------------------------------------------------------
# CytoPedia page  (/cytopedia)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class _CytopediaSelectors:
    # URL path suffix
    cytopedia_path: str = "/cytopedia"

    # Search textbox accessible name
    search_accessible_name: str = "Search terms by title or description"

    # Category filter button
    entities_button: str = "Entities"

    # Category result link after filtering
    cell_entities_link: str = "Cell Entities"


# ---------------------------------------------------------------------------
# Module-level singletons (import these everywhere)
# ---------------------------------------------------------------------------
login_sel = _LoginSelectors()
ready_sel = _AppReadySelectors()
programs_sel = _ProgramsSelectors()
inventory_sel = _InventorySelectors()
dx_sel = _DxSelectors()
cytopedia_sel = _CytopediaSelectors()
