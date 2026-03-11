"""
Journey catalog: registry of all available user journeys.

Usage::

    from src.ui.journeys.journey_catalog import catalog
    journey_fn = catalog.get("programs")
    await journey_fn(page, user)
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable

from src.ui.journeys.cytopedia_journey import run_cytopedia_journey
from src.ui.journeys.dx_journey import run_dx_journey
from src.ui.journeys.inventory_journey import run_inventory_journey
from src.ui.journeys.programs_journey import run_programs_journey

# Type alias: each journey is an async callable (page, user) -> None
Journey = Callable[..., Awaitable[None]]


class JourneyCatalog:
    def __init__(self) -> None:
        self._items: dict[str, Journey] = {}

    def register(self, name: str, journey: Journey) -> "JourneyCatalog":
        self._items[name] = journey
        return self

    def get(self, name: str) -> Journey:
        if name not in self._items:
            raise KeyError(
                f"Journey '{name}' not registered. Available: {list(self._items)}"
            )
        return self._items[name]

    def all_names(self) -> list[str]:
        return list(self._items.keys())


# ---------------------------------------------------------------------------
# Default catalog – all production journeys registered
# ---------------------------------------------------------------------------
catalog = (
    JourneyCatalog()
    .register("programs", run_programs_journey)
    .register("inventory", run_inventory_journey)
    .register("dx", run_dx_journey)
    .register("cytopedia", run_cytopedia_journey)
)
