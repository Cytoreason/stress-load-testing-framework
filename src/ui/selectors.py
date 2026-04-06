"""
Validated UI selectors for the CytoReason platform.

VALIDATION NOTES
----------------
All selectors were validated against the LIVE staging environment:

  https://apps.private.cytoreason.com/platform/customers/pyy/

Validation method: Playwright headless Chromium, authenticated session,
full page inspection across all target pages (2026-03-11).

SELECTOR STRATEGY
-----------------
Priority order (most to least stable):
  1. ARIA role + accessible name  → get_by_role(role, name=...)
  2. Label text                   → get_by_label(label)
  3. has_text filter              → locator(...).filter(has_text=...)
  4. Visible text content         → get_by_text(text)
  5. Test ID attribute            → get_by_test_id(id)  [not yet used in app]
  6. CSS class / ID               [last resort – avoid]

LIVE VALIDATION RESULTS (2026-03-11)
-------------------------------------
  ✓ Auth0 login labels ("Email address *", "Password *", "Continue")
  ✓ App ready signal: link "Programs"
  ✓ Programs search textbox (matched by placeholder via accessible name)
  ✓ Programs "My Projects" / "All Projects" buttons
  ✓ CytoPedia search textbox
  ✓ CytoPedia "Entities" filter button
  ✓ CytoPedia "Cell Entities" result button
  ✓ DX page model button (filter has_text "Disease Model")
  ✓ DX analysis radios: "Target Gene", "Target Signature", "Meta Analysis", "Per Dataset"
  ✓ DX filter comboboxes: "bronchus", "expression differences"
  ✓ DX "Inventory" side-nav link
  ✓ Inventory "Disease Biology" category button
  ✓ Inventory items after Disease Biology expansion (format "N.Item Name")

CORRECTED FROM INITIAL ASSUMPTIONS
------------------------------------
  - ASTH combobox has NO aria-label → must use has_text filter, not get_by_role(name=...)
  - "Disease Models" button does NOT exist → the model name button IS the picker
  - "White Space" radio does NOT exist → real toggles: Target Gene / Target Signature
  - Filter "disease vs control" is WRONG → actual: "expression differences: disease vs healthy"
  - Inventory items format is "N.Item Name" (NO spaces around dot)
  - Only 6 Disease Biology items exist for ASTH (items 7/8 do not exist)

Re-validation: Run `pytest -m selector` before every load/stress run.
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
# Inventory page  (URL: /disease-explorer/model-inventory/<model-slug>)
# Accessed by clicking the "Inventory" side-nav link on the DX page.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class _InventorySelectors:
    # Side-nav link visible on DX page → navigates to inventory
    inventory_link_name: str = "Inventory"

    # Category toggle button (expands the list of inventory items)
    disease_biology_button: str = "Disease Biology"

    # Inventory items after Disease Biology expansion.
    # LIVE VALIDATED format: "N.Item Name" (NO spaces around the dot).
    # These are both links and buttons in the DOM; use locator filter or link role.
    item_target_expression: str = "Target Expression in Disease"
    item_target_regulation: str = "Target Regulation in Disease"
    item_cell_abundance: str = "Differential Cell Abundance in Disease"
    item_target_cell_assoc: str = "Target-Cell Association"
    item_target_pathway_assoc: str = "Target-Pathway Association"
    item_diff_expression_diseases: str = "Differential expression across diseases"


# ---------------------------------------------------------------------------
# Disease Explorer / DX page  (/disease-explorer/differential-expression)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class _DxSelectors:
    # URL path suffix for the Differential Expression view
    de_path: str = "/disease-explorer/differential-expression"

    # Model picker button.
    # LIVE VALIDATED: the button shows the current model name inline, e.g.
    # "ASTH\nDisease Model\nAsthma". It has NO aria-label.
    # Selector: locator("button").filter(has_text=model_picker_has_text).first
    model_picker_has_text: str = "Disease Model"

    # Analysis type toggles (role="radio" buttons – NOT HTML radio inputs).
    # LIVE VALIDATED present on DX page: Target Gene, Target Signature,
    # Meta Analysis, Per Dataset.  "White Space" does NOT exist.
    radio_target_gene: str = "Target Gene"
    radio_target_signature: str = "Target Signature"
    radio_meta_analysis: str = "Meta Analysis"
    radio_per_dataset: str = "Per Dataset"

    # Filter comboboxes (Radix UI select triggers, no aria-label).
    # Identified by has_text of their current value.
    # LIVE VALIDATED default values on the ASTH DE view:
    combobox_tissue_has_text: str = "bronchus"
    combobox_comparison_has_text: str = "expression differences"

    # Model names used in the model picker dropdown.
    # After clicking the model picker button, these appear as clickable items.
    # LIVE VALIDATED dropdown items (format: "<ABBR><Full Name>" no space):
    #   ASTHAsthma, CECeliac Disease, COPDChronic Obstructive Pulmonary Disease,
    #   CDCrohn's Disease, SSCSystemic Sclerosis, UCUlcerative Colitis
    copd_dropdown_has_text: str = "Chronic Obstructive Pulmonary Disease"
    uc_dropdown_has_text: str = "Ulcerative Colitis"


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
